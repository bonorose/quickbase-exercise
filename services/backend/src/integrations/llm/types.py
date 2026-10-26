#!/usr/bin/env python3
# ******************************************************************************
# * @file    integrations/llm/types.py
# * @author  Simeon Marlokov
# * @brief   Vendor-neutral LLM types. Services depend on these and on LLMClient,
# *          never on a provider SDK, so swapping vendors means one new adapter.
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    name: str
    result: dict[str, Any]


@dataclass(frozen=True)
class LLMMessage:
    """One turn. ``raw`` is the provider payload needed to replay thought signatures."""

    role: Literal["user", "assistant", "tool"]
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()
    raw: Any | None = None
    model: str | None = None


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class Notice:
    """Transient availability info (retrying, switching model) worth showing to the user."""

    message: str


@dataclass(frozen=True)
class Completed:
    """Final event for the diagnostic ``/llm/stream`` endpoint, which does not use tools."""

    text: str
    model: str


@dataclass(frozen=True)
class TurnComplete:
    """Final event for an agent turn. May include tool calls."""

    turn: LLMMessage


LLMEvent = TextDelta | Notice | Completed | TurnComplete


class LLMError(Exception):
    """The provider failed (overloaded, timed out, rejected the request)."""


class LLMUnavailableError(LLMError):
    """The provider is overloaded or unreachable. Retrying later may work."""


class LLMQuotaExhaustedError(LLMError):
    """A daily quota is used up. Retrying before the reset does not help."""

    def __init__(self, message: str, resets_in_seconds: float):
        super().__init__(message)
        self.resets_in_seconds = resets_in_seconds


class LLMClient(Protocol):
    @property
    def model(self) -> str: ...

    def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> AsyncIterator[LLMEvent]:
        """Yields Notice* then TextDelta*.

        With no tools, finishes with exactly one Completed.
        With tools, finishes with exactly one TurnComplete, or raises LLMError.
        """
        ...
