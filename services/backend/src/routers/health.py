#!/usr/bin/env python3
# ******************************************************************************
# * @file    health.py
# * @author  Simeon Marlokov
# * @brief   Health route
# * @date    25.10.2026
# ******************************************************************************
from fastapi import APIRouter

from src.dependencies.health import HealthControllerDep
from src.schemas.health.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(controller: HealthControllerDep):
    return await controller.health()


@router.get("/livez")
async def livez():
    return {"status": "ok"}
