#!/usr/bin/env python3
# ******************************************************************************
# * @file    health_service.py
# * @author  Simeon Marlokov
# * @brief   Service health checks
# * @date    25.10.2026
# ******************************************************************************
from loguru import logger

from src.repositories.health_repository import HealthRepository


class HealthService:
    def __init__(self, repository: HealthRepository):
        self.repository = repository

    async def is_database_up(self) -> bool:
        try:
            return await self.repository.ping()
        except Exception as exc:
            logger.warning(f"Database health check failed: {exc}")
            return False
