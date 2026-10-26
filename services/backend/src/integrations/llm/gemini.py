#!/usr/bin/env python3
# ******************************************************************************
# * @file    integrations/llm/gemini.py
# * @author  Simeon Marlokov
# * @brief   Gemini adapter (google-genai) for LLMClient, with streaming,
# *          a first-chunk timeout per attempt, retry and model fallback.
# * @date    25.10.2026
# ******************************************************************************
import asyncio
import contextlib
import random
import time
import uuid
from collections.abc import AsyncIterator

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from src.integrations.llm.types import (
    Completed,
    LLMEvent,
    LLMMessage,
    LLMQuotaExhaustedError,
    LLMUnavailableError,
    Notice,
    TextDelta,
    ToolCall,
    ToolSpec,
    TurnComplete,
)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
# After a fallback succeeds, keep using that model for a while so one conversation doesn't flap
STICKY_FALLBACK_SECONDS = 300
# Used when a per-day quota error carries no RetryInfo
DEFAULT_QUOTA_RESET_SECONDS = 3600
# Gemini accepts this placeholder when replaying a function call produced by a different model.
FOREIGN_SIGNATURE = b"skip_thought_signature_validator"


def _describe(exc: Exception) -> str:
    if isinstance(exc, genai_errors.APIError):
        return f"HTTP {exc.code}"
    if isinstance(exc, TimeoutError):
        return "no response in time"
    return "timed out"


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.APIError):
        return exc.code in RETRYABLE_STATUS
    return isinstance(exc, (httpx.TimeoutException, asyncio.TimeoutError))


def _backoff(attempt: int) -> float:
    return min(2.0 * 2**attempt, 30.0) + random.random()


def _daily_quota_reset_seconds(exc: Exception) -> float | None:
    """Seconds until reset when `exc` is a 429 for a per-day quota (retrying is pointless until then);
    None for anything else, including per-minute rate limits, which are worth a quick retry.

    Shape: error.details[] holds a google.rpc.QuotaFailure whose violations[].quotaId contains
    "PerDay" (e.g. GenerateRequestsPerDayPerProjectPerModel-FreeTier) and a google.rpc.RetryInfo
    with retryDelay like "68228s"."""
    if not isinstance(exc, genai_errors.APIError) or exc.code != 429 or not isinstance(exc.details, dict):
        return None
    details = exc.details.get("error", exc.details).get("details") or []
    per_day = any(
        "PerDay" in violation.get("quotaId", "") for detail in details for violation in detail.get("violations") or []
    )
    if not per_day:
        return None
    for detail in details:
        delay = str(detail.get("retryDelay", ""))
        with contextlib.suppress(ValueError):
            return float(delay.removesuffix("s"))
    return DEFAULT_QUOTA_RESET_SECONDS


def _format_duration(seconds: float) -> str:
    minutes = max(1, round(seconds / 60))
    return f"{minutes} min" if minutes < 60 else f"{minutes // 60} h {minutes % 60:02d} min"


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        fallback_models: list[str],
        first_chunk_timeout_seconds: float,
        request_timeout_seconds: float,
        max_retries: int,
        temperature: float,
    ):
        self._model = model
        self.fallback_models = [m for m in fallback_models if m != model]
        self.first_chunk_timeout_seconds = first_chunk_timeout_seconds
        self.max_retries = max_retries
        self.temperature = temperature
        # The SDK uses this value twice: as the httpx per-read timeout and as the X-Server-Timeout
        # header (Google's deadline for the whole generation). So it must cover a full long answer;
        # detecting an overloaded/hung model is the job of the much shorter first-chunk timeout.
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(request_timeout_seconds * 1000)),
        )
        self._sticky: str | None = None
        self._sticky_until = 0.0
        # model -> monotonic time its daily quota resets; such models are left out of the plan
        self._quota_exhausted_until: dict[str, float] = {}

    @property
    def model(self) -> str:
        return self._model

    # ------ Model selection
    def _plan(self) -> list[tuple[str, int]]:
        """Ordered (model, attempt) pairs to try, without models whose daily quota is used up."""
        now = time.monotonic()
        models = [self._model, *self.fallback_models]
        if self._sticky and now < self._sticky_until:
            models = [self._sticky, *[m for m in models if m != self._sticky]]
        models = [m for m in models if self._quota_exhausted_until.get(m, 0.0) <= now]
        return [(m, attempt) for m in models for attempt in range(self.max_retries + 1)]

    def _all_quotas_exhausted_error(self) -> LLMQuotaExhaustedError:
        now = time.monotonic()
        models = [self._model, *self.fallback_models]
        resets_in = min(self._quota_exhausted_until.get(m, now) for m in models) - now
        return LLMQuotaExhaustedError(
            f"The daily Gemini quota is used up for {', '.join(models)}. "
            f"It resets in about {_format_duration(resets_in)}.",
            resets_in_seconds=resets_in,
        )

    def _record_success(self, model: str) -> None:
        if model == self._model:
            self._sticky = None
        elif model != self._sticky:
            self._sticky, self._sticky_until = model, time.monotonic() + STICKY_FALLBACK_SECONDS

    @staticmethod
    def _next_index(plan: list[tuple[str, int]], i: int, exc: Exception) -> int:
        """An explicit 503/429 is retried on the same model; a hang skips to the next model, if any."""
        if isinstance(exc, genai_errors.APIError):
            return i + 1
        j = i + 1
        while j < len(plan) and plan[j][0] == plan[i][0]:
            j += 1
        return j if j < len(plan) else i + 1

    # ------ Conversions
    @staticmethod
    def _config(system: str | None, tools: list[ToolSpec], temperature: float) -> types.GenerateContentConfig:
        kwargs: dict = {"system_instruction": system, "temperature": temperature}
        if tools:
            kwargs["tools"] = [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=spec.name,
                            description=spec.description,
                            parameters_json_schema=spec.parameters,
                        )
                        for spec in tools
                    ]
                )
            ]
            kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
        return types.GenerateContentConfig(**kwargs)

    @staticmethod
    def _to_contents(messages: list[LLMMessage], model: str) -> list[types.Content]:
        contents: list[types.Content] = []
        for turn in messages:
            if turn.role == "tool":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(name=result.name, response=result.result)
                            for result in turn.tool_results
                        ],
                    )
                )
                continue
            if turn.role == "assistant" and turn.raw is not None and turn.model == model:
                contents.append(turn.raw)
                continue
            if turn.role == "assistant" and (turn.tool_calls or turn.raw is not None):
                parts: list[types.Part] = []
                if turn.text:
                    parts.append(types.Part(text=turn.text))
                signature = FOREIGN_SIGNATURE if turn.model != model else None
                for call in turn.tool_calls:
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(id=call.id, name=call.name, args=call.args),
                            thought_signature=signature,
                        )
                    )
                contents.append(types.Content(role="model", parts=parts or [types.Part(text=turn.text)]))
                continue
            role = "model" if turn.role == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=turn.text)]))
        return contents

    @staticmethod
    def serialize_raw(raw: types.Content | None) -> dict | None:
        if raw is None:
            return None
        return raw.model_dump(mode="json")

    @staticmethod
    def deserialize_raw(payload: dict | None) -> types.Content | None:
        if not payload:
            return None
        return types.Content.model_validate(payload)

    # ------ Streaming
    async def _open_stream(
        self, model: str, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> tuple[AsyncIterator[types.GenerateContentResponse], types.GenerateContentResponse | None]:
        """Start a stream and pull its first chunk. Overload errors can surface on the first chunk,
        so pulling it here lets the caller still retry/fall back before anything is forwarded."""
        response = await self._client.aio.models.generate_content_stream(model=model, contents=contents, config=config)
        chunks = aiter(response)
        try:
            return chunks, await anext(chunks, None)
        except BaseException:
            # Includes cancellation by the first-chunk timeout: release the HTTP stream
            with contextlib.suppress(Exception):
                await chunks.aclose()
            raise

    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> AsyncIterator[LLMEvent]:
        tool_list = list(tools or [])
        config = self._config(system, tool_list, self.temperature)
        plan = self._plan()
        if not plan:
            raise self._all_quotas_exhausted_error()

        # Tell the caller something right away; otherwise nothing arrives until the first token
        yield Notice(f"Waiting for {plan[0][0]}…")

        model, chunks, first = None, None, None
        i = 0
        while i < len(plan):
            candidate, attempt = plan[i]
            contents = self._to_contents(messages, candidate)
            try:
                chunks, first = await asyncio.wait_for(
                    self._open_stream(candidate, contents, config),
                    timeout=self.first_chunk_timeout_seconds,
                )
                model = candidate
                break
            except Exception as exc:
                if not _is_retryable(exc):
                    raise LLMUnavailableError(f"Gemini rejected the request ({candidate}): {exc}") from exc

                reset_seconds = _daily_quota_reset_seconds(exc)
                if reset_seconds is not None:
                    # No point retrying this model until tomorrow: remember it and move on
                    self._quota_exhausted_until[candidate] = time.monotonic() + reset_seconds
                    next_i = next((j for j in range(i + 1, len(plan)) if plan[j][0] != candidate), len(plan))
                    if next_i >= len(plan):
                        if not self._plan():
                            raise self._all_quotas_exhausted_error() from exc
                        raise LLMQuotaExhaustedError(
                            f"Gemini is unavailable right now ({candidate}: daily quota used up). "
                            "Please try again in a minute.",
                            resets_in_seconds=reset_seconds,
                        ) from exc
                    yield Notice(f"{candidate} has used up its daily quota, switching to {plan[next_i][0]}…")
                    i = next_i
                    continue

                next_i = self._next_index(plan, i, exc)
                if next_i >= len(plan):
                    tried = ", ".join(dict.fromkeys(m for m, _ in plan))
                    raise LLMUnavailableError(
                        f"Gemini is unavailable right now ({candidate}: {_describe(exc)}; tried {tried}). "
                        "Please try again in a minute."
                    ) from exc
                next_model = plan[next_i][0]
                if next_model == candidate:
                    yield Notice(f"{candidate} is busy ({_describe(exc)}), retrying…")
                    await asyncio.sleep(_backoff(attempt))
                else:
                    yield Notice(f"{candidate} is busy ({_describe(exc)}), switching to {next_model}…")
                i = next_i
        self._record_success(model)

        collected: list[types.Part] = []
        calls: list[ToolCall] = []
        visible: list[str] = []
        try:
            for chunk in [first] if first is not None else []:
                for delta in self._absorb(chunk, collected, calls, capture_calls=bool(tool_list)):
                    visible.append(delta.text)
                    yield delta
            async for chunk in chunks:
                for delta in self._absorb(chunk, collected, calls, capture_calls=bool(tool_list)):
                    visible.append(delta.text)
                    yield delta
        except (genai_errors.APIError, httpx.TimeoutException) as exc:
            raise LLMUnavailableError(f"Gemini stream interrupted ({model}: {_describe(exc)}). Please retry.") from exc

        text = "".join(visible)
        if tool_list:
            yield TurnComplete(
                LLMMessage(
                    role="assistant",
                    text=text,
                    tool_calls=tuple(calls),
                    raw=types.Content(role="model", parts=collected),
                    model=model,
                )
            )
            return
        yield Completed(text=text, model=model)

    @staticmethod
    def _absorb(
        chunk: types.GenerateContentResponse,
        collected: list[types.Part],
        calls: list[ToolCall],
        *,
        capture_calls: bool,
    ) -> list[TextDelta]:
        """Merge consecutive plain-text parts. Thought and signed parts stay intact and are not spoken."""
        if not chunk.candidates or not chunk.candidates[0].content:
            return []
        deltas: list[TextDelta] = []
        for part in chunk.candidates[0].content.parts or []:
            if part.function_call and capture_calls:
                function_call = part.function_call
                call_id = function_call.id or uuid.uuid4().hex
                calls.append(ToolCall(id=call_id, name=function_call.name or "", args=dict(function_call.args or {})))
                collected.append(part)
                continue
            if part.thought or part.thought_signature:
                collected.append(part)
                continue
            if part.text:
                deltas.append(TextDelta(part.text))
                previous = collected[-1] if collected else None
                if (
                    previous is not None
                    and previous.text
                    and not previous.thought
                    and not previous.function_call
                    and not previous.thought_signature
                ):
                    collected[-1] = types.Part(text=(previous.text or "") + part.text)
                else:
                    collected.append(types.Part(text=part.text))
                continue
            collected.append(part)
        return deltas
