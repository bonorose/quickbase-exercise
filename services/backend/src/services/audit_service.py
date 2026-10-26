#!/usr/bin/env python3
# ******************************************************************************
# * @file    audit_service.py
# * @author  Simeon Marlokov
# * @brief   Audit reads. Operators see their own rows; team leads see the
# *          organization.
# * @date    25.10.2026
# ******************************************************************************
import uuid

from src.core.exceptions import NotFoundError
from src.core.organization import OrganizationContext
from src.repositories.audit_repository import AuditRepository
from src.repositories.ticket_repository import TicketRepository
from src.schemas.audit.response import present_audit


class AuditService:
    def __init__(self, audit: AuditRepository, tickets: TicketRepository, organization: OrganizationContext):
        self.audit = audit
        self.tickets = tickets
        self.organization = organization

    async def list_events(
        self,
        *,
        session_id: uuid.UUID | None,
        ticket_id: int | None,
        limit: int,
        offset: int,
    ):
        if ticket_id is not None and await self.tickets.get_visible(ticket_id) is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        rows, total = await self.audit.list_visible(
            role=self.organization.role,
            user_id=self.organization.user_id,
            session_id=session_id,
            ticket_id=ticket_id,
            limit=limit,
            offset=offset,
        )
        return [present_audit(row) for row in rows], total
