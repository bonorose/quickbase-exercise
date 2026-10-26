#!/usr/bin/env python3
# ******************************************************************************
# * @file    audit/response.py
# * @author  Simeon Marlokov
# * @brief   Audit list body (C-11).
# * @date    25.10.2026
# ******************************************************************************
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel

from src.models.audit_event import AuditEvent
from src.schemas.tickets.response import UserRef


class AuditEventResponse(BaseModel):
    id: int
    actor_type: Literal["user", "agent", "system"]
    actor: UserRef | None
    event: str
    session_id: str | None
    ticket_id: int | None
    pending_revision_id: str | None
    payload: dict[str, Any]
    date_created: int


class AuditListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int


def _unix(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def present_audit(row: AuditEvent) -> AuditEventResponse:
    actor = None if row.actor is None else UserRef(id=row.actor.id, name=row.actor.name)
    return AuditEventResponse(
        id=row.id,
        actor_type=row.actor_type,  # type: ignore[arg-type]
        actor=actor,
        event=row.event,
        session_id=None if row.session_id is None else str(row.session_id),
        ticket_id=row.ticket_id,
        pending_revision_id=None if row.pending_revision_id is None else str(row.pending_revision_id),
        payload=dict(row.payload or {}),
        date_created=_unix(row.date_created),
    )
