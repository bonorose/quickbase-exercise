#!/usr/bin/env python3
# ******************************************************************************
# * @file    item_repository.py
# * @author  Simeon Marlokov
# * @brief   Item data access
# * @date    25.10.2026
# ******************************************************************************
from sqlalchemy import select

from src.models.item import Item
from src.repositories.base_repository import BaseRepository


class ItemRepository(BaseRepository[Item]):
    model = Item

    async def get_by_name(self, name: str) -> Item | None:
        return await self.session.scalar(select(Item).where(Item.name == name))
