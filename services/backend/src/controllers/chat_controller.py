#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat_controller.py
# * @author  Simeon Marlokov
# * @brief   Chat controller: sessions to C-05–C-07 and the C-20 stream.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from datetime import UTC, datetime

from fastapi.responses import StreamingResponse

from src.core.rate_limit import enforce_write_limit
from src.core.sse import sse_response
from src.models.chat_message import ChatMessage
from src.models.chat_session import ChatSession
from src.schemas.chat.request import CreateSessionRequest, SendMessageRequest, SessionListQuery
from src.schemas.chat.response import (
    ChatSessionDetailResponse,
    ChatSessionListResponse,
    ChatSessionResponse,
    apply_pending_statuses,
    render_messages,
)
from src.services.chat_service import ChatService


def unix_seconds(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def _session(chat: ChatSession) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=str(chat.id),
        title=chat.title,
        date_created=unix_seconds(chat.date_created),
        last_activity_at=unix_seconds(chat.last_activity_at),
    )


class ChatController:
    def __init__(self, service: ChatService):
        self.service = service

    async def create_session(self, request: CreateSessionRequest) -> ChatSessionResponse:
        return _session(await self.service.create_session(request.title))

    async def list_sessions(self, query: SessionListQuery) -> ChatSessionListResponse:
        items, total = await self.service.list_sessions(query.limit, query.offset)
        return ChatSessionListResponse(
            items=[_session(item) for item in items],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    async def get_session(self, session_id: uuid.UUID) -> ChatSessionDetailResponse:
        chat, messages = await self.service.get_session(session_id)
        body = _session(chat)
        rendered = render_messages(
            [
                (message.id, message.role, message.content, message.model, unix_seconds(message.date_created))
                for message in messages
                if isinstance(message, ChatMessage)
            ]
        )
        draft_ids = [
            part.pending_revision_id
            for message in rendered
            for part in message.parts
            if getattr(part, "pending_revision_id", None)
        ]
        statuses = await self.service.pending_statuses([item for item in draft_ids if item])
        return ChatSessionDetailResponse(**body.model_dump(), messages=apply_pending_statuses(rendered, statuses))

    async def send_message(self, session_id: uuid.UUID, request: SendMessageRequest) -> StreamingResponse:
        enforce_write_limit(self.service.organization)
        await self.service.open_stream(session_id)
        return sse_response(self.service.stream_message(session_id, request.text))
