#!/usr/bin/env python3
# ******************************************************************************
# * @file    items/response.py
# * @author  Simeon Marlokov
# * @brief   Item response bodies
# * @date    25.10.2026
# ******************************************************************************
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    limit: int
    offset: int
