#!/usr/bin/env python3
# ******************************************************************************
# * @file    base_repository.py
# * @author  Simeon Marlokov
# * @brief   Generic CRUD repository over an ORM model
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base


class BaseRepository[ModelT: Base]:
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, limit: int, offset: int) -> Sequence[ModelT]:
        query = select(self.model).order_by(self.model.id).limit(limit).offset(offset)
        return (await self.session.scalars(query)).all()

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(self.model))

    async def create(self, **values: Any) -> ModelT:
        entity = self.model(**values)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelT, **values: Any) -> ModelT:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.commit()
