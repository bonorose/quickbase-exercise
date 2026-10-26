#!/usr/bin/env python3
# ******************************************************************************
# * @file    organization.py
# * @author  Simeon Marlokov
# * @brief   Authenticated organization scope. Never taken from a request body.
# * @date    25.10.2026
# ******************************************************************************
from dataclasses import dataclass


@dataclass(frozen=True)
class OrganizationContext:
    organization_id: int
    user_id: int
    role: str
