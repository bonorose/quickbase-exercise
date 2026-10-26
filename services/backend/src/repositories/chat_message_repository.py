#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat_message_repository.py
# * @author  Simeon Marlokov
# * @brief   Messages for sessions the caller owns. Writes bump last_activity_at.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from src.models.chat_message import ChatMessage
from src.models.chat_session import ChatSession
from src.repositories.organization_scoped_repository import OrganizationScopedRepository
from src.schemas.chat.storage import StoredMessage


class ChatMessageRepository(OrganizationScopedRepository[ChatMessage]):
    model = ChatMessage

    async def list_for_session(self, session_id: uuid.UUID) -> Sequence[ChatMessage]:
        query = self._select().where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
        return (await self.session.scalars(query)).all()

    async def append(
        self,
        chat: ChatSession,
        *,
        role: str,
        content: dict[str, Any],
        model: str | None = None,
    ) -> ChatMessage:
        StoredMessage.model_validate(content)
        message = ChatMessage(
            session_id=chat.id,
            organization_id=self.organization.organization_id,
            role=role,
            content=content,
            model=model,
        )
        self.session.add(message)
        chat.last_activity_at = datetime.now(UTC)
        await self._commit()
        return message
