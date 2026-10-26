#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat_session_repository.py
# * @author  Simeon Marlokov
# * @brief   Chat sessions scoped to the organization and the owning user.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from collections.abc import Sequence

from sqlalchemy import func, select

from src.models.chat_session import ChatSession
from src.repositories.organization_scoped_repository import OrganizationScopedRepository


class ChatSessionRepository(OrganizationScopedRepository[ChatSession]):
    model = ChatSession

    def _select(self):
        return super()._select().where(ChatSession.user_id == self.organization.user_id)

    async def create_session(self, title: str) -> ChatSession:
        return await self.create(title=title, user_id=self.organization.user_id)

    async def list_for_user(self, limit: int, offset: int) -> Sequence[ChatSession]:
        query = self._select().order_by(ChatSession.last_activity_at.desc()).limit(limit).offset(offset)
        return (await self.session.scalars(query)).all()

    async def count_for_user(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(self._select().subquery())) or 0

    async def get_owned(self, session_id: uuid.UUID) -> ChatSession | None:
        return await self.session.scalar(self._select().where(ChatSession.id == session_id))

    async def get_in_organization(self, session_id: uuid.UUID) -> ChatSession | None:
        """Organization-wide lookup for system notes. HTTP reads stay on get_owned."""
        query = select(ChatSession).where(
            ChatSession.organization_id == self.organization.organization_id,
            ChatSession.id == session_id,
        )
        return await self.session.scalar(query)
