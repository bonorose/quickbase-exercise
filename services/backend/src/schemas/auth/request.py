#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth/request.py
# * @author  Simeon Marlokov
# * @brief   Auth request bodies
# * @date    25.10.2026
# ******************************************************************************
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)
