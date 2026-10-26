#!/usr/bin/env python3
# ******************************************************************************
# * @file    revision_repository.py
# * @author  Simeon Marlokov
# * @brief   Organization-scoped revision history. M1 only reads it.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from collections.abc import Sequence

from sqlalchemy.orm import selectinload

from src.models.revision import Revision
from src.repositories.organization_scoped_repository import OrganizationScopedRepository


class RevisionRepository(OrganizationScopedRepository[Revision]):
    model = Revision

    async def list_for_ticket(self, ticket_id: int) -> Sequence[Revision]:
        query = (
            self._select()
            .where(Revision.ticket_id == ticket_id)
            .order_by(Revision.date_created, Revision.id)
            .options(selectinload(Revision.user))
        )
        return (await self.session.scalars(query)).all()

    async def latest_id(self, ticket_id: int) -> uuid.UUID | None:
        query = (
            self._select()
            .where(Revision.ticket_id == ticket_id)
            .order_by(Revision.date_created.desc(), Revision.id.desc())
            .limit(1)
        )
        row = await self.session.scalar(query)
        return None if row is None else row.id
