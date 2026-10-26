#!/usr/bin/env python3
# ******************************************************************************
# * @file    pending_revisions/response.py
# * @author  Simeon Marlokov
# * @brief   Pending revision bodies (C-09, C-10, C-15, C-17, C-18, C-19).
# * @date    25.10.2026
# ******************************************************************************
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.models.pending_revision import PendingRevision
from src.models.ticket import Ticket, TicketPriority, TicketStatus
from src.schemas.tickets.response import PendingRevisionSummary, TicketResponse, UserRef

SNAPSHOT_FIELDS = ("title", "contents", "status", "priority")


class FieldDiff(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from")
    to: str


class TicketRef(BaseModel):
    id: int
    title: str


class PendingRevisionResponse(BaseModel):
    id: str
    ticket: TicketRef
    action: Literal["update", "delete"]
    origin: Literal["human", "agent"]
    owner: UserRef
    session_id: str | None
    previous_revision_id: str | None
    changed_contents: dict[str, Any]
    diff: dict[str, FieldDiff]
    tainted: bool
    status: Literal["open", "executed", "rejected", "expired"]
    expires_at: int | None
    server_time: int
    decided_by: UserRef | None
    decided_at: int | None
    date_created: int
    date_updated: int
    result: dict[str, Any] | None


class ApproveResponse(BaseModel):
    pending_revision: PendingRevisionResponse
    ticket: TicketResponse


def unix_seconds(value: datetime | None) -> int | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def snapshot(ticket: Ticket) -> dict[str, str]:
    return {
        "title": ticket.title,
        "contents": ticket.contents,
        "status": TicketStatus(ticket.status).name,
        "priority": TicketPriority(ticket.priority).name,
    }


def merge_contents(base: dict[str, str], partial: dict[str, Any]) -> dict[str, str]:
    merged = dict(base)
    for key in SNAPSHOT_FIELDS:
        value = partial.get(key)
        if value is not None:
            merged[key] = value
    return merged


def field_diff(current: dict[str, str], changed: dict[str, Any]) -> dict[str, dict[str, str]]:
    diff: dict[str, dict[str, str]] = {}
    for key, value in changed.items():
        if key not in SNAPSHOT_FIELDS or value is None:
            continue
        before = str(current.get(key, ""))
        after = str(value)
        if before != after:
            diff[key] = {"from": before, "to": after}
    return diff


def present_pending(draft: PendingRevision, ticket: Ticket | None, *, now: datetime | None = None) -> dict[str, Any]:
    current = snapshot(ticket) if ticket is not None else {}
    clock = now or datetime.now(UTC)
    body = PendingRevisionResponse(
        id=str(draft.id),
        ticket=TicketRef(id=draft.ticket_id, title="" if ticket is None else ticket.title),
        action=draft.action,  # type: ignore[arg-type]
        origin=draft.origin,  # type: ignore[arg-type]
        owner=UserRef(id=draft.owner.id, name=draft.owner.name),
        session_id=None if draft.session_id is None else str(draft.session_id),
        previous_revision_id=None if draft.previous_revision_id is None else str(draft.previous_revision_id),
        changed_contents=dict(draft.changed_contents or {}),
        diff=field_diff(current, draft.changed_contents or {}),
        tainted=draft.tainted,
        status=draft.status,  # type: ignore[arg-type]
        expires_at=unix_seconds(draft.expires_at),
        server_time=unix_seconds(clock) or 0,
        decided_by=None if draft.decider is None else UserRef(id=draft.decider.id, name=draft.decider.name),
        decided_at=unix_seconds(draft.decided_at),
        date_created=unix_seconds(draft.date_created) or 0,
        date_updated=unix_seconds(draft.date_updated) or 0,
        result=draft.result,
    )
    return body.model_dump(mode="json", by_alias=True)


def present_summary(draft: PendingRevision) -> PendingRevisionSummary:
    return PendingRevisionSummary(
        id=str(draft.id),
        owner=UserRef(id=draft.owner.id, name=draft.owner.name),
        origin=draft.origin,  # type: ignore[arg-type]
        tainted=draft.tainted,
        status=draft.status,  # type: ignore[arg-type]
        expires_at=unix_seconds(draft.expires_at),
    )
