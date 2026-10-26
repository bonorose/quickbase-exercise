#!/usr/bin/env python3
# ******************************************************************************
# * @file    audit/request.py
# * @author  Simeon Marlokov
# * @brief   Audit list query (C-11).
# * @date    25.10.2026
# ******************************************************************************
import uuid

from pydantic import BaseModel, Field


class AuditListQuery(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    session_id: uuid.UUID | None = None
    ticket_id: int | None = Field(default=None, ge=1)
