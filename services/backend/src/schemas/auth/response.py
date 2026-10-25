#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth/response.py
# * @author  Simeon Marlokov
# * @brief   Auth response bodies
# * @date    25.10.2026
# ******************************************************************************
from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
