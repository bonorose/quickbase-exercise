#!/usr/bin/env python3
# ******************************************************************************
# * @file    organization_repository.py
# * @author  Simeon Marlokov
# * @brief   Organization data access. The table is isolated by its own id under RLS.
# * @date    25.10.2026
# ******************************************************************************
from sqlalchemy import select

from src.models.organization import Organization
from src.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    async def get_by_name(self, name: str) -> Organization | None:
        return await self.session.scalar(select(Organization).where(Organization.name == name))
