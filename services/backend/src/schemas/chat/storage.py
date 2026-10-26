#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat/storage.py
# * @author  Simeon Marlokov
# * @brief   JSON stored in chat_messages.content. ``raw`` and ``model_result``
# *          never leave the server.
# * @date    25.10.2026
# ******************************************************************************
from typing import Any, Literal

from pydantic import BaseModel, Field


class StoredTextPart(BaseModel):
    kind: Literal["text"] = "text"
    text: str


class StoredToolPart(BaseModel):
    kind: Literal["tool"] = "tool"
    call_id: str
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    ok: bool | None = None
    result: dict[str, Any] | None = None
    model_result: dict[str, Any] | None = None
    error: str | None = None
    pending_revision_id: str | None = None
    pending_revision_status: str | None = None
    untrusted: bool = False


class StoredMessage(BaseModel):
    parts: list[StoredTextPart | StoredToolPart]
    raw: dict[str, Any] | None = None
