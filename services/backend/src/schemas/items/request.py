#!/usr/bin/env python3
# ******************************************************************************
# * @file    items/request.py
# * @author  Simeon Marlokov
# * @brief   Item request bodies
# * @date    25.10.2026
# ******************************************************************************
from pydantic import BaseModel, Field


class ItemCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ItemUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
