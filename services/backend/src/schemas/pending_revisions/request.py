#!/usr/bin/env python3
# ******************************************************************************
# * @file    pending_revisions/request.py
# * @author  Simeon Marlokov
# * @brief   Claim, save, approve, and reject bodies. Unknown fields are 422.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.tickets.response import TicketPriorityName, TicketStatusName


class ChangedContents(BaseModel):
    """Partial editable snapshot. description, ids, and organization_id are rejected."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    contents: str | None = Field(default=None, max_length=2000)
    status: TicketStatusName | None = None
    priority: TicketPriorityName | None = None


class ClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["update", "delete"]
    changed_contents: ChangedContents | None = None


class SaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changed_contents: ChangedContents
    action: Literal["update", "delete"] | None = None


class ApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changed_contents: ChangedContents | None = None
    action: Literal["update", "delete"] | None = None


class RejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=500)


class PendingListQuery(BaseModel):
    status: Literal["open", "executed", "rejected", "expired", "all"] = "open"
    ticket_id: int | None = Field(default=None, ge=1)
    session_id: uuid.UUID | None = None
    scope: Literal["mine", "lead_queue"] = "mine"
