#!/usr/bin/env python3
# ******************************************************************************
# * @file    llm/request.py
# * @author  Simeon Marlokov
# * @brief   LLM request bodies
# * @date    25.10.2026
# ******************************************************************************
from pydantic import BaseModel, Field


class LLMStreamRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
