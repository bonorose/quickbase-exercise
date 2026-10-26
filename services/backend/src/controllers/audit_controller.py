#!/usr/bin/env python3
# ******************************************************************************
# * @file    audit_controller.py
# * @author  Simeon Marlokov
# * @brief   Audit list (C-11).
# * @date    25.10.2026
# ******************************************************************************
from src.schemas.audit.request import AuditListQuery
from src.schemas.audit.response import AuditListResponse
from src.services.audit_service import AuditService


class AuditController:
    def __init__(self, service: AuditService):
        self.service = service

    async def list_events(self, query: AuditListQuery) -> AuditListResponse:
        items, total = await self.service.list_events(
            session_id=query.session_id,
            ticket_id=query.ticket_id,
            limit=query.limit,
            offset=query.offset,
        )
        return AuditListResponse(items=items, total=total)
