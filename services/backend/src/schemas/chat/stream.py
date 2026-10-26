#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat/stream.py
# * @author  Simeon Marlokov
# * @brief   C-20 events. ``approval_required`` is defined for M3 and not emitted yet.
# * @date    25.10.2026
# ******************************************************************************
from typing import Any, Literal

from pydantic import BaseModel


class SessionStreamEvent(BaseModel):
    type: Literal["session"] = "session"
    session_id: str


class StatusStreamEvent(BaseModel):
    type: Literal["status"] = "status"
    message: str


class DeltaStreamEvent(BaseModel):
    type: Literal["delta"] = "delta"
    text: str


class ToolCallStreamEvent(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    call_id: str
    name: str
    args: dict[str, Any]


class ToolResultStreamEvent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    call_id: str
    ok: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class ApprovalRequiredStreamEvent(BaseModel):
    """mutate_ticket created or updated a draft. The turn may continue."""

    type: Literal["approval_required"] = "approval_required"
    call_id: str
    pending_revision: dict[str, Any]


class DoneStreamEvent(BaseModel):
    type: Literal["done"] = "done"
    message_id: str
    model: str


class ErrorStreamEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
    code: Literal["llm_unavailable", "quota_exhausted", "internal"] | None = None


ChatStreamEvent = (
    SessionStreamEvent
    | StatusStreamEvent
    | DeltaStreamEvent
    | ToolCallStreamEvent
    | ToolResultStreamEvent
    | ApprovalRequiredStreamEvent
    | DoneStreamEvent
    | ErrorStreamEvent
)
