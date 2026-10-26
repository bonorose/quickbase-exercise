#!/usr/bin/env python3
# ******************************************************************************
# * @file    pending_revision_controller.py
# * @author  Simeon Marlokov
# * @brief   Pending revision HTTP: claim, save, decide, list.
# * @date    25.10.2026
# ******************************************************************************
import uuid

from src.controllers.ticket_controller import to_ticket_response
from src.core.rate_limit import enforce_write_limit
from src.schemas.pending_revisions.request import (
    ApproveRequest,
    ClaimRequest,
    PendingListQuery,
    RejectRequest,
    SaveRequest,
)
from src.schemas.pending_revisions.response import ApproveResponse, PendingRevisionResponse
from src.services.pending_revision_service import PendingRevisionService


class PendingRevisionController:
    def __init__(self, service: PendingRevisionService):
        self.service = service

    async def claim(self, ticket_id: int, request: ClaimRequest) -> PendingRevisionResponse:
        body = await self.service.claim(ticket_id, request.action, request.changed_contents)
        return PendingRevisionResponse.model_validate(body)

    async def save(self, draft_id: uuid.UUID, request: SaveRequest) -> PendingRevisionResponse:
        body = await self.service.save(draft_id, request.changed_contents, request.action)
        return PendingRevisionResponse.model_validate(body)

    async def approve(self, draft_id: uuid.UUID, request: ApproveRequest) -> ApproveResponse:
        enforce_write_limit(self.service.organization)
        body, ticket, revisions, discussions = await self.service.approve(
            draft_id, request.changed_contents, request.action
        )
        return ApproveResponse(
            pending_revision=PendingRevisionResponse.model_validate(body),
            ticket=to_ticket_response(ticket, revisions, discussions, open_pending_revision=None),
        )

    async def reject(self, draft_id: uuid.UUID, request: RejectRequest) -> PendingRevisionResponse:
        body = await self.service.reject(draft_id, request.reason)
        return PendingRevisionResponse.model_validate(body)

    async def get(self, draft_id: uuid.UUID) -> PendingRevisionResponse:
        return PendingRevisionResponse.model_validate(await self.service.get(draft_id))

    async def list_drafts(self, query: PendingListQuery) -> list[PendingRevisionResponse]:
        rows = await self.service.list_drafts(
            status=query.status,
            ticket_id=query.ticket_id,
            session_id=query.session_id,
            scope=query.scope,
        )
        return [PendingRevisionResponse.model_validate(row) for row in rows]
