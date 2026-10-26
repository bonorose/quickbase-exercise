#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat/response.py
# * @author  Simeon Marlokov
# * @brief   Chat session bodies (C-05, C-06, C-07). Tool rows are folded into
# *          the preceding assistant message. Provider ``raw`` is never returned.
# * @date    25.10.2026
# ******************************************************************************
from typing import Any, Literal

from pydantic import BaseModel

from src.schemas.chat.storage import StoredMessage, StoredTextPart, StoredToolPart


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    date_created: int
    last_activity_at: int


class ChatSessionListResponse(BaseModel):
    items: list[ChatSessionResponse]
    total: int
    limit: int
    offset: int


class TextPart(BaseModel):
    kind: Literal["text"] = "text"
    text: str


class ToolPart(BaseModel):
    kind: Literal["tool"] = "tool"
    call_id: str
    name: str
    args: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None
    pending_revision_id: str | None = None
    pending_revision_status: str | None = None


class ChatMessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant", "system"]
    parts: list[TextPart | ToolPart]
    model: str | None
    date_created: int


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: list[ChatMessageResponse]


def render_messages(rows: list[tuple[int, str, dict, str | None, int]]) -> list[ChatMessageResponse]:
    """Fold ``role=tool`` rows into the previous assistant message's tool parts."""
    rendered: list[ChatMessageResponse] = []
    for message_id, role, content, model, date_created in rows:
        stored = StoredMessage.model_validate(content)
        if role == "tool" and rendered and rendered[-1].role == "assistant":
            by_call = {part.call_id: part for part in rendered[-1].parts if isinstance(part, ToolPart)}
            for part in stored.parts:
                if not isinstance(part, StoredToolPart):
                    continue
                target = by_call.get(part.call_id)
                if target is None:
                    continue
                target.result = part.result
                target.error = part.error
                target.pending_revision_id = part.pending_revision_id
                target.pending_revision_status = part.pending_revision_status
            continue
        if role == "tool":
            continue
        parts: list[TextPart | ToolPart] = []
        for part in stored.parts:
            if isinstance(part, StoredTextPart):
                parts.append(TextPart(text=part.text))
            else:
                parts.append(
                    ToolPart(
                        call_id=part.call_id,
                        name=part.name,
                        args=part.args,
                        pending_revision_id=part.pending_revision_id,
                        pending_revision_status=part.pending_revision_status,
                    )
                )
        rendered.append(
            ChatMessageResponse(
                id=message_id,
                role=role,  # type: ignore[arg-type]
                parts=parts,
                model=model,
                date_created=date_created,
            )
        )
    return rendered


def apply_pending_statuses(messages: list[ChatMessageResponse], statuses: dict[str, str]) -> list[ChatMessageResponse]:
    """C-07 reads the live draft status onto tool parts."""
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolPart) and part.pending_revision_id:
                current = statuses.get(part.pending_revision_id)
                if current is not None:
                    part.pending_revision_status = current
    return messages
