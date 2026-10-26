#!/usr/bin/env python3
# ******************************************************************************
# * @file    audit_repository.py
# * @author  Simeon Marlokov
# * @brief   Append-only audit inserts and organization-scoped reads.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from src.models.audit_event import AuditEvent
from src.models.chat_session import ChatSession
from src.repositories.organization_scoped_repository import OrganizationScopedRepository


class AuditRepository(OrganizationScopedRepository[AuditEvent]):
    model = AuditEvent

    def stage(
        self,
        *,
        actor_type: str,
        event: str,
        actor_id: int | None = None,
        session_id: uuid.UUID | None = None,
        ticket_id: int | None = None,
        pending_revision_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditEvent:
        row = AuditEvent(
            organization_id=self.organization.organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event=event,
            session_id=session_id,
            ticket_id=ticket_id,
            pending_revision_id=pending_revision_id,
            payload=payload or {},
        )
        self.session.add(row)
        return row

    def _filtered(self, *, role: str, user_id: int, session_id: uuid.UUID | None, ticket_id: int | None):
        query = self._select()
        if role != "team_lead":
            owned = select(ChatSession.id).where(
                ChatSession.organization_id == self.organization.organization_id,
                ChatSession.user_id == user_id,
            )
            query = query.where(or_(AuditEvent.actor_id == user_id, AuditEvent.session_id.in_(owned)))
        if session_id is not None:
            query = query.where(AuditEvent.session_id == session_id)
        if ticket_id is not None:
            query = query.where(AuditEvent.ticket_id == ticket_id)
        return query

    async def list_visible(
        self,
        *,
        role: str,
        user_id: int,
        session_id: uuid.UUID | None,
        ticket_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[AuditEvent], int]:
        filtered = self._filtered(role=role, user_id=user_id, session_id=session_id, ticket_id=ticket_id)
        total = await self.session.scalar(select(func.count()).select_from(filtered.subquery())) or 0
        rows = await self.session.scalars(
            filtered.options(selectinload(AuditEvent.actor))
            .order_by(AuditEvent.date_created.desc(), AuditEvent.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return rows.all(), int(total)
