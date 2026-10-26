#!/usr/bin/env python3
# ******************************************************************************
# * @file    tickets/response.py
# * @author  Simeon Marlokov
# * @brief   Ticket list and detail bodies (C-03, C-04)
# * @date    25.10.2026
# ******************************************************************************
from typing import Literal

from pydantic import BaseModel

TicketStatusName = Literal["open", "blocked", "closed"]
TicketPriorityName = Literal["lowest", "low", "medium", "high", "critical"]


class UserRef(BaseModel):
    id: int
    name: str


class TicketSummary(BaseModel):
    id: int
    status: TicketStatusName
    priority: TicketPriorityName
    title: str
    description: str
    date_updated: int


class TicketListResponse(BaseModel):
    items: list[TicketSummary]
    total: int
    limit: int
    offset: int


class EditableSnapshot(BaseModel):
    title: str
    contents: str
    status: TicketStatusName
    priority: TicketPriorityName


class RevisionResponse(BaseModel):
    id: str
    user: UserRef
    initial_contents: EditableSnapshot
    changed_contents: EditableSnapshot
    date_created: int


class DiscussionResponse(BaseModel):
    id: int
    user: UserRef
    contents: str


class PendingRevisionSummary(BaseModel):
    id: str
    owner: UserRef
    origin: Literal["human", "agent"]
    tainted: bool
    status: Literal["open", "executed", "rejected", "expired"]
    expires_at: int | None


class TicketResponse(TicketSummary):
    contents: str
    submitted_by: str
    date_created: int
    updated_by: UserRef | None
    revisions: list[RevisionResponse]
    discussions: list[DiscussionResponse]
    open_pending_revision: PendingRevisionSummary | None = None
