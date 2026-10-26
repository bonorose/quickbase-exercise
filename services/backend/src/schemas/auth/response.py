#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth/response.py
# * @author  Simeon Marlokov
# * @brief   Auth response bodies (C-01, C-02)
# * @date    25.10.2026
# ******************************************************************************
from typing import Literal

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class OrganizationResponse(BaseModel):
    id: int
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: Literal["operator", "team_lead"]
    organization: OrganizationResponse
