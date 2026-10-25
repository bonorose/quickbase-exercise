#!/usr/bin/env python3
# ******************************************************************************
# * @file    health_controller.py
# * @author  Simeon Marlokov
# * @brief   Health controller
# * @date    25.10.2026
# ******************************************************************************
from src.schemas.health.response import HealthResponse
from src.services.health_service import HealthService


class HealthController:
    def __init__(self, service: HealthService):
        self.service = service

    async def health(self) -> HealthResponse:
        db_up = await self.service.is_database_up()
        return HealthResponse(status="ok" if db_up else "degraded", database="up" if db_up else "down")
