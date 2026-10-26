#!/usr/bin/env python3
# ******************************************************************************
# * @file    pending_revision_repository.py
# * @author  Simeon Marlokov
# * @brief   Organization-scoped drafts. One open draft per ticket.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import selectinload

from src.models.pending_revision import PendingRevision
from src.repositories.organization_scoped_repository import OrganizationScopedRepository

_LOADED = (
    selectinload(PendingRevision.owner),
    selectinload(PendingRevision.decider),
)


class PendingRevisionRepository(OrganizationScopedRepository[PendingRevision]):
    model = PendingRevision

    def _loaded(self):
        return self._select().options(*_LOADED)

    async def get_loaded(self, draft_id: uuid.UUID) -> PendingRevision | None:
        return await self.session.scalar(self._loaded().where(PendingRevision.id == draft_id))

    async def lock(self, draft_id: uuid.UUID) -> PendingRevision | None:
        query = self._loaded().where(PendingRevision.id == draft_id).with_for_update(of=PendingRevision)
        return await self.session.scalar(query)

    async def lock_open_for_ticket(self, ticket_id: int) -> PendingRevision | None:
        query = (
            self._loaded()
            .where(PendingRevision.ticket_id == ticket_id, PendingRevision.status == "open")
            .with_for_update(of=PendingRevision)
        )
        return await self.session.scalar(query)

    async def open_for_ticket(self, ticket_id: int) -> PendingRevision | None:
        query = self._loaded().where(PendingRevision.ticket_id == ticket_id, PendingRevision.status == "open")
        return await self.session.scalar(query)

    async def lock_due(self, now: datetime) -> Sequence[PendingRevision]:
        query = (
            self._loaded()
            .where(
                PendingRevision.status == "open",
                PendingRevision.expires_at.is_not(None),
                PendingRevision.expires_at <= now,
            )
            .with_for_update(of=PendingRevision)
        )
        return (await self.session.scalars(query)).all()

    async def statuses(self, ids: list[uuid.UUID]) -> dict[str, str]:
        if not ids:
            return {}
        rows = await self.session.scalars(self._select().where(PendingRevision.id.in_(ids)))
        return {str(row.id): row.status for row in rows}

    async def list_matching(
        self,
        *,
        user_id: int | None,
        status: str | None,
        ticket_id: int | None,
        session_id: uuid.UUID | None,
        tainted: bool | None,
        limit: int,
    ) -> Sequence[PendingRevision]:
        query = self._loaded().order_by(PendingRevision.date_updated.desc(), PendingRevision.id.desc())
        if user_id is not None:
            query = query.where(PendingRevision.user_id == user_id)
        if status is not None:
            query = query.where(PendingRevision.status == status)
        if ticket_id is not None:
            query = query.where(PendingRevision.ticket_id == ticket_id)
        if session_id is not None:
            query = query.where(PendingRevision.session_id == session_id)
        if tainted is not None:
            query = query.where(PendingRevision.tainted.is_(tainted))
        return (await self.session.scalars(query.limit(limit))).all()
