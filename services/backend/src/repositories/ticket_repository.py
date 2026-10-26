#!/usr/bin/env python3
# ******************************************************************************
# * @file    ticket_repository.py
# * @author  Simeon Marlokov
# * @brief   Organization-scoped ticket queries. Deleted tickets are invisible.
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import Sequence

from sqlalchemy import func, literal, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from src.models.ticket import Ticket
from src.repositories.organization_scoped_repository import OrganizationScopedRepository

SORTS = {
    "-date_updated": (Ticket.date_updated.desc(), Ticket.id.desc()),
    "date_updated": (Ticket.date_updated.asc(), Ticket.id.asc()),
    "priority": (Ticket.priority.asc(), Ticket.id.asc()),
    "-priority": (Ticket.priority.desc(), Ticket.id.desc()),
    "id": (Ticket.id.asc(),),
}


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def like_pattern(value: str) -> str:
    return f"%{escape_like(value)}%"


def ticket_document():
    """Same expression as the trigram GIN index, so ILIKE can use it."""
    space = literal(" ")
    return Ticket.title.op("||")(space).op("||")(Ticket.description).op("||")(space).op("||")(Ticket.contents)


class TicketRepository(OrganizationScopedRepository[Ticket]):
    model = Ticket

    def _select(self) -> Select:
        return super()._select().where(Ticket.date_deleted.is_(None))

    async def search(
        self,
        *,
        q: str | None,
        status: int | None,
        priority: int | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Ticket], int]:
        filtered = self._select()
        if q:
            filtered = filtered.where(ticket_document().ilike(like_pattern(q), escape="\\"))
        if status is not None:
            filtered = filtered.where(Ticket.status == status)
        if priority is not None:
            filtered = filtered.where(Ticket.priority == priority)
        total = await self.session.scalar(select(func.count()).select_from(filtered.subquery())) or 0
        rows = await self.session.scalars(filtered.order_by(*SORTS[sort]).limit(limit).offset(offset))
        return rows.all(), int(total)

    async def get_visible(self, ticket_id: int) -> Ticket | None:
        query = self._select().where(Ticket.id == ticket_id).options(selectinload(Ticket.updated_by_user))
        return await self.session.scalar(query)

    async def lock_visible(self, ticket_id: int) -> Ticket | None:
        query = self._select().where(Ticket.id == ticket_id).with_for_update()
        return await self.session.scalar(query)

    async def get_any(self, ticket_id: int) -> Ticket | None:
        """Includes soft-deleted tickets so an executed deletion can still be shown once."""
        query = (
            select(Ticket)
            .where(Ticket.organization_id == self.organization.organization_id, Ticket.id == ticket_id)
            .options(selectinload(Ticket.updated_by_user))
        )
        return await self.session.scalar(query)
