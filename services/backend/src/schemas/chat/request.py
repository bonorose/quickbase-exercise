#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat/request.py
# * @author  Simeon Marlokov
# * @brief   Chat session and message requests (C-05, C-06, C-08)
# * @date    25.10.2026
# ******************************************************************************
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class SessionListQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
