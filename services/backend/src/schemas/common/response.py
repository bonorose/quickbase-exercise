#!/usr/bin/env python3
# ******************************************************************************
# * @file    common/response.py
# * @author  Simeon Marlokov
# * @brief   Response bodies shared across categories
# * @date    25.10.2026
# ******************************************************************************
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
