#!/usr/bin/env python3
# ******************************************************************************
# * @file    discussion_repository.py
# * @author  Simeon Marlokov
# * @brief   Organization-scoped discussions, ordered by id. No write API in v1.
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import Sequence

from sqlalchemy.orm import selectinload

from src.models.discussion import Discussion
from src.repositories.organization_scoped_repository import OrganizationScopedRepository


class DiscussionRepository(OrganizationScopedRepository[Discussion]):
    model = Discussion

    async def list_for_ticket(self, ticket_id: int) -> Sequence[Discussion]:
        query = (
            self._select()
            .where(Discussion.ticket_id == ticket_id)
            .order_by(Discussion.id)
            .options(selectinload(Discussion.user))
        )
        return (await self.session.scalars(query)).all()
