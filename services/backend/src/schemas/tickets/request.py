#!/usr/bin/env python3
# ******************************************************************************
# * @file    tickets/request.py
# * @author  Simeon Marlokov
# * @brief   Ticket list query (C-03)
# * @date    25.10.2026
# ******************************************************************************
from typing import Literal

from pydantic import BaseModel, Field


class TicketListQuery(BaseModel):
    q: str | None = Field(default=None, max_length=200)
    status: Literal["open", "blocked", "closed"] | None = None
    priority: Literal["lowest", "low", "medium", "high", "critical"] | None = None
    sort: Literal["-date_updated", "date_updated", "priority", "-priority", "id"] = "-date_updated"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
