#!/usr/bin/env python3
# ******************************************************************************
# * @file    integrations/llm/fake.py
# * @author  Simeon Marlokov
# * @brief   Scripted LLM. The last user message selects a YAML turn. No Gemini call.
# * @date    25.10.2026
# ******************************************************************************
import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

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


def normalize_prompt(text: str) -> str:
    return " ".join(text.lower().split())


@dataclass
class ScriptedTurn:
    notices: list[str] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    text: str = ""
    error: str | None = None
    delay: float = 0.0


def _turn(payload: dict[str, Any], index: int) -> ScriptedTurn:
    calls = []
    for offset, call in enumerate(payload.get("tool_calls") or []):
        calls.append(
            ToolCall(
                id=str(call.get("id") or f"call-{index}-{offset}"),
                name=str(call["name"]),
                args=dict(call.get("args") or {}),
            )
        )
    return ScriptedTurn(
        notices=list(payload.get("notices") or []),
        tool_calls=calls,
        text=str(payload.get("text") or ""),
        error=payload.get("error"),
        delay=float(payload.get("delay") or 0),
    )


def load_scripts(path: str | None) -> dict[str, ScriptedTurn]:
    if not path:
        return {}
    root = Path(path)
    files = [root] if root.is_file() else sorted(root.glob("*.yaml"))
    scripts: dict[str, ScriptedTurn] = {}
    for file in files:
        if not file.is_file():
            continue
        loaded = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
        for key, payload in (loaded.get("scripts") or {}).items():
            scripts[normalize_prompt(str(key))] = _turn(payload or {}, len(scripts))
    return scripts


class ScriptedLLMClient:
    """Maps the last user message to one scripted turn, then a text follow-up after tools."""

    def __init__(self, scripts: dict[str, ScriptedTurn] | None = None, model: str = "fake-model"):
        self.scripts = scripts or {}
        self._model = model

    @classmethod
    def from_path(cls, path: str | None) -> "ScriptedLLMClient":
        return cls(load_scripts(path))

    @property
    def model(self) -> str:
        return self._model

    def _script_for(self, messages: list[LLMMessage]) -> ScriptedTurn | None:
        for message in reversed(messages):
            if message.role == "user" and message.text:
                return self.scripts.get(normalize_prompt(message.text))
        return None

    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> AsyncIterator[LLMEvent]:
        script = self._script_for(messages)
        last = messages[-1] if messages else None
        follow_up = script is not None and last is not None and last.role == "tool"
        if script and script.delay:
            await asyncio.sleep(script.delay)
        if script and script.error and not follow_up:
            self._raise(script)
        if script and script.tool_calls and not follow_up and tools:
            for notice in script.notices:
                yield Notice(notice)
            yield TurnComplete(
                LLMMessage(role="assistant", text="", tool_calls=tuple(script.tool_calls), model=self._model)
            )
            return
        text = script.text if script else (last.text if last and last.role == "user" else "")
        if not tools:
            if text:
                yield TextDelta(text)
            yield Completed(text=text, model=self._model)
            return
        for notice in script.notices if script else []:
            yield Notice(notice)
        if text:
            yield TextDelta(text)
        yield TurnComplete(LLMMessage(role="assistant", text=text, model=self._model))

    def _raise(self, script: ScriptedTurn) -> None:
        if script.error == "quota_exhausted":
            raise LLMQuotaExhaustedError(
                "The daily Gemini quota is used up. It resets in about 1 h 00 min.",
                resets_in_seconds=3600,
            )
        raise LLMUnavailableError(script.error or "The model is unavailable.")
