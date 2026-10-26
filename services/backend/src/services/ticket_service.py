#!/usr/bin/env python3
# ******************************************************************************
# * @file    ticket_service.py
# * @author  Simeon Marlokov
# * @brief   Ticket reads. Another organization's ticket is NotFoundError.
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import Sequence
from dataclasses import dataclass

from src.core.exceptions import NotFoundError
from src.models.discussion import Discussion
from src.models.revision import Revision
from src.models.ticket import PRIORITY_NAMES, STATUS_NAMES, TICKET_SORTS, Ticket, TicketPriority, TicketStatus
from src.repositories.discussion_repository import DiscussionRepository
from src.repositories.revision_repository import RevisionRepository
from src.repositories.ticket_repository import TicketRepository

MAX_LIMIT = 100


@dataclass(frozen=True)
class TicketDetail:
    ticket: Ticket
    revisions: Sequence[Revision]
    discussions: Sequence[Discussion]


class TicketService:
    def __init__(
        self,
        tickets: TicketRepository,
        revisions: RevisionRepository,
        discussions: DiscussionRepository,
    ):
        self.tickets = tickets
        self.revisions = revisions
        self.discussions = discussions

    async def list_tickets(
        self,
        *,
        q: str | None,
        status: str | None,
        priority: str | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Ticket], int]:
        term = q.strip() if q else None
        if sort not in TICKET_SORTS:
            raise ValueError(f"Unknown sort '{sort}'")
        if status is not None and status not in STATUS_NAMES:
            raise ValueError(f"Unknown status '{status}'")
        if priority is not None and priority not in PRIORITY_NAMES:
            raise ValueError(f"Unknown priority '{priority}'")
        return await self.tickets.search(
            q=term or None,
            status=None if status is None else TicketStatus[status].value,
            priority=None if priority is None else TicketPriority[priority].value,
            sort=sort,
            limit=min(limit, MAX_LIMIT),
            offset=offset,
        )

    async def search_for_agent(
        self,
        *,
        q: str,
        status: str | None,
        priority: str | None,
        limit: int,
    ) -> list[tuple[Ticket, Sequence[Discussion]]]:
        """Organization-scoped search plus the three most recent discussions on each hit."""
        tickets, _total = await self.list_tickets(
            q=q,
            status=status,
            priority=priority,
            sort="-date_updated",
            limit=limit,
            offset=0,
        )
        found: list[tuple[Ticket, Sequence[Discussion]]] = []
        for ticket in tickets:
            discussions = await self.discussions.list_for_ticket(ticket.id)
            found.append((ticket, discussions[-3:]))
        return found

    async def get_ticket(self, ticket_id: int) -> TicketDetail:
        ticket = await self.tickets.get_visible(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        revisions = await self.revisions.list_for_ticket(ticket_id)
        discussions = await self.discussions.list_for_ticket(ticket_id)
        return TicketDetail(ticket=ticket, revisions=revisions, discussions=discussions)
