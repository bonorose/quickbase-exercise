#!/usr/bin/env python3
# ******************************************************************************
# * @file    health_repository.py
# * @author  Simeon Marlokov
# * @brief   Database connectivity probe
# * @date    25.10.2026
# ******************************************************************************
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ping(self) -> bool:
        return await self.session.scalar(text("SELECT 1")) == 1
