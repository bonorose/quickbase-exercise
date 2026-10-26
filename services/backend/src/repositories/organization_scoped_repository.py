#!/usr/bin/env python3
# ******************************************************************************
# * @file    organization_scoped_repository.py
# * @author  Simeon Marlokov
# * @brief   Repository base that always filters by the authenticated organization.
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.core.organization import OrganizationContext
from src.models.base import Base
from src.repositories.base_repository import BaseRepository


class OrganizationScopedRepository[ModelT: Base](BaseRepository[ModelT]):
    """Every query starts from ``_select()``. Subclasses must not call ``select(Model)``."""

    def __init__(self, session: AsyncSession, organization: OrganizationContext):
        super().__init__(session)
        self.organization = organization

    def _select(self) -> Select:
        return select(self.model).where(self.model.organization_id == self.organization.organization_id)

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        return await self.session.scalar(self._select().where(self.model.id == entity_id))

    async def list(self, limit: int, offset: int) -> Sequence[ModelT]:
        query = self._select().order_by(self.model.id).limit(limit).offset(offset)
        return (await self.session.scalars(query)).all()

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(self._select().subquery())) or 0

    async def create(self, **values: Any) -> ModelT:
        if "organization_id" in values:
            raise ValueError("organization_id is taken from the authenticated organization")
        values["organization_id"] = self.organization.organization_id
        return await super().create(**values)

    async def update(self, entity: ModelT, **values: Any) -> ModelT:
        if "organization_id" in values:
            raise ValueError("organization_id cannot be changed")
        return await super().update(entity, **values)
