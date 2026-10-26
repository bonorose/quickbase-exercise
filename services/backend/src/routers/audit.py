#!/usr/bin/env python3
# ******************************************************************************
# * @file    audit.py
# * @author  Simeon Marlokov
# * @brief   Audit route (C-11).
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import APIRouter, Query

from src.dependencies.audit import AuditControllerDep
from src.schemas.audit.request import AuditListQuery
from src.schemas.audit.response import AuditListResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
async def list_audit_events(controller: AuditControllerDep, query: Annotated[AuditListQuery, Query()]):
    return await controller.list_events(query)
