#!/usr/bin/env python3
# ******************************************************************************
# * @file    tickets.py
# * @author  Simeon Marlokov
# * @brief   Ticket routes (C-03, C-04). Writes go through pending revisions later.
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import APIRouter, Query, status

from src.dependencies.pending_revisions import PendingRevisionControllerDep
from src.dependencies.tickets import TicketControllerDep
from src.schemas.common.response import ErrorResponse
from src.schemas.pending_revisions.request import ClaimRequest
from src.schemas.pending_revisions.response import PendingRevisionResponse
from src.schemas.tickets.request import TicketListQuery
from src.schemas.tickets.response import TicketListResponse, TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}


@router.get("", response_model=TicketListResponse)
async def list_tickets(controller: TicketControllerDep, query: Annotated[TicketListQuery, Query()]):
    return await controller.list_tickets(query)


@router.get("/{ticket_id}", response_model=TicketResponse, responses=NOT_FOUND)
async def get_ticket(ticket_id: int, controller: TicketControllerDep):
    return await controller.get_ticket(ticket_id)


@router.post(
    "/{ticket_id}/pending-revisions",
    response_model=PendingRevisionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        **NOT_FOUND,
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
async def claim_pending_revision(
    ticket_id: int,
    request: ClaimRequest,
    controller: PendingRevisionControllerDep,
):
    return await controller.claim(ticket_id, request)
