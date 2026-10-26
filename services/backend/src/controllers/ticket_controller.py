#!/usr/bin/env python3
# ******************************************************************************
# * @file    ticket_controller.py
# * @author  Simeon Marlokov
# * @brief   Ticket controller: entities -> C-03 / C-04 schemas
# * @date    25.10.2026
# ******************************************************************************
from datetime import UTC, datetime

from src.models.discussion import Discussion
from src.models.revision import Revision
from src.models.ticket import Ticket, TicketPriority, TicketStatus
from src.models.user import User
from src.schemas.tickets.request import TicketListQuery
from src.schemas.tickets.response import (
    DiscussionResponse,
    EditableSnapshot,
    RevisionResponse,
    TicketListResponse,
    TicketResponse,
    TicketSummary,
    UserRef,
)
from src.services.ticket_service import TicketDetail, TicketService


def unix_seconds(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def _user_ref(user: User | None) -> UserRef | None:
    if user is None:
        return None
    return UserRef(id=user.id, name=user.name)


def _snapshot(payload: dict) -> EditableSnapshot:
    return EditableSnapshot.model_validate(payload)


def _summary(ticket: Ticket) -> TicketSummary:
    return TicketSummary(
        id=ticket.id,
        status=TicketStatus(ticket.status).name,
        priority=TicketPriority(ticket.priority).name,
        title=ticket.title,
        description=ticket.description,
        date_updated=unix_seconds(ticket.date_updated),
    )


def _revision(revision: Revision) -> RevisionResponse:
    return RevisionResponse(
        id=str(revision.id),
        user=UserRef(id=revision.user.id, name=revision.user.name),
        initial_contents=_snapshot(revision.initial_contents),
        changed_contents=_snapshot(revision.changed_contents),
        date_created=unix_seconds(revision.date_created),
    )


def _discussion(discussion: Discussion) -> DiscussionResponse:
    return DiscussionResponse(
        id=discussion.id,
        user=UserRef(id=discussion.user.id, name=discussion.user.name),
        contents=discussion.contents,
    )


def to_ticket_response(ticket, revisions, discussions, open_pending_revision) -> TicketResponse:
    summary = _summary(ticket)
    return TicketResponse(
        **summary.model_dump(),
        contents=ticket.contents,
        submitted_by=ticket.submitted_by,
        date_created=unix_seconds(ticket.date_created),
        updated_by=_user_ref(ticket.updated_by_user),
        revisions=[_revision(revision) for revision in revisions],
        discussions=[_discussion(discussion) for discussion in discussions],
        open_pending_revision=open_pending_revision,
    )


class TicketController:
    def __init__(self, service: TicketService, drafts=None):
        self.service = service
        self.drafts = drafts

    async def list_tickets(self, query: TicketListQuery) -> TicketListResponse:
        tickets, total = await self.service.list_tickets(
            q=query.q,
            status=query.status,
            priority=query.priority,
            sort=query.sort,
            limit=query.limit,
            offset=query.offset,
        )
        return TicketListResponse(
            items=[_summary(ticket) for ticket in tickets],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    async def get_ticket(self, ticket_id: int) -> TicketResponse:
        detail: TicketDetail = await self.service.get_ticket(ticket_id)
        summary = None if self.drafts is None else await self.drafts.open_summary(ticket_id)
        return to_ticket_response(detail.ticket, detail.revisions, detail.discussions, summary)
