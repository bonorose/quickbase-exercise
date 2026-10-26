#!/usr/bin/env python3
# ******************************************************************************
# * @file    agent/events.py
# * @author  Simeon Marlokov
# * @brief   Events the agent loop yields. The chat service maps them to C-20.
# * @date    25.10.2026
# ******************************************************************************
from dataclasses import dataclass

from src.integrations.llm.types import LLMMessage, ToolCall
from src.tools.base import ToolOutcome


@dataclass(frozen=True)
class AgentStatus:
    message: str


@dataclass(frozen=True)
class AgentDelta:
    text: str


@dataclass(frozen=True)
class AgentModelTurn:
    """A finished model turn. Persisted before its tool calls run."""

    turn: LLMMessage


@dataclass(frozen=True)
class AgentToolCall:
    call: ToolCall


@dataclass(frozen=True)
class AgentToolResult:
    call_id: str
    outcome: ToolOutcome


@dataclass(frozen=True)
class AgentApprovalRequired:
    """mutate_ticket created or updated a draft. The turn continues."""

    call_id: str
    pending_revision: dict


@dataclass(frozen=True)
class AgentDone:
    model: str
    text: str
    turn: LLMMessage


AgentEvent = (
    AgentStatus | AgentDelta | AgentModelTurn | AgentToolCall | AgentToolResult | AgentApprovalRequired | AgentDone
)
