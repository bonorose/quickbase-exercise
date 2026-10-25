#!/usr/bin/env python3
# ******************************************************************************
# * @file    health/response.py
# * @author  Simeon Marlokov
# * @brief   Health response bodies
# * @date    25.10.2026
# ******************************************************************************
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
