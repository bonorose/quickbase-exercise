#!/usr/bin/env python3
# ******************************************************************************
# * @file    item_service.py
# * @author  Simeon Marlokov
# * @brief   Item business logic
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import Sequence

from src.core.exceptions import ConflictError, NotFoundError
from src.models.item import Item
from src.repositories.item_repository import ItemRepository


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    async def list_items(self, limit: int, offset: int) -> tuple[Sequence[Item], int]:
        return await self.repository.list(limit, offset), await self.repository.count()

    async def get_item(self, item_id: int) -> Item:
        item = await self.repository.get_by_id(item_id)
        if item is None:
            raise NotFoundError(f"Item {item_id} not found")
        return item

    async def create_item(self, name: str, description: str | None) -> Item:
        await self._ensure_name_available(name)
        return await self.repository.create(name=name, description=description)

    async def update_item(self, item_id: int, changes: dict) -> Item:
        item = await self.get_item(item_id)
        if "name" in changes and changes["name"] != item.name:
            await self._ensure_name_available(changes["name"])
        return await self.repository.update(item, **changes)

    async def delete_item(self, item_id: int) -> None:
        await self.repository.delete(await self.get_item(item_id))

    async def _ensure_name_available(self, name: str) -> None:
        if await self.repository.get_by_name(name) is not None:
            raise ConflictError(f"Item with name '{name}' already exists")
