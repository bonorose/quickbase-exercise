#!/usr/bin/env python3
# ******************************************************************************
# * @file    pending_revisions.py
# * @author  Simeon Marlokov
# * @brief   Pending revision routes (C-09, C-10, C-15, C-18, C-19).
# * @date    25.10.2026
# ******************************************************************************
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Query, status

from src.dependencies.pending_revisions import PendingRevisionControllerDep
from src.schemas.common.response import ErrorResponse
from src.schemas.pending_revisions.request import ApproveRequest, PendingListQuery, RejectRequest, SaveRequest
from src.schemas.pending_revisions.response import ApproveResponse, PendingRevisionResponse

router = APIRouter(prefix="/pending-revisions", tags=["pending-revisions"])

ERRORS = {
    status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_410_GONE: {"model": ErrorResponse},
}


@router.get("", response_model=list[PendingRevisionResponse], responses=ERRORS)
async def list_pending_revisions(
    controller: PendingRevisionControllerDep,
    query: Annotated[PendingListQuery, Query()],
):
    return await controller.list_drafts(query)


@router.get("/{pending_revision_id}", response_model=PendingRevisionResponse, responses=ERRORS)
async def get_pending_revision(pending_revision_id: uuid.UUID, controller: PendingRevisionControllerDep):
    return await controller.get(pending_revision_id)


@router.put("/{pending_revision_id}", response_model=PendingRevisionResponse, responses=ERRORS)
async def save_pending_revision(
    pending_revision_id: uuid.UUID,
    request: SaveRequest,
    controller: PendingRevisionControllerDep,
):
    return await controller.save(pending_revision_id, request)


@router.post("/{pending_revision_id}/approve", response_model=ApproveResponse, responses=ERRORS)
async def approve_pending_revision(
    pending_revision_id: uuid.UUID,
    controller: PendingRevisionControllerDep,
    request: ApproveRequest = Body(default_factory=ApproveRequest),
):
    return await controller.approve(pending_revision_id, request)


@router.post("/{pending_revision_id}/reject", response_model=PendingRevisionResponse, responses=ERRORS)
async def reject_pending_revision(
    pending_revision_id: uuid.UUID,
    controller: PendingRevisionControllerDep,
    request: RejectRequest = Body(default_factory=RejectRequest),
):
    return await controller.reject(pending_revision_id, request)
