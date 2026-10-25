#!/usr/bin/env python3
# ******************************************************************************
# * @file    item_controller.py
# * @author  Simeon Marlokov
# * @brief   Item controller: request schemas -> service calls -> response schemas
# * @date    25.10.2026
# ******************************************************************************
from src.schemas.items.request import ItemCreateRequest, ItemUpdateRequest
from src.schemas.items.response import ItemListResponse, ItemResponse
from src.services.item_service import ItemService


class ItemController:
    def __init__(self, service: ItemService):
        self.service = service

    async def list_items(self, limit: int, offset: int) -> ItemListResponse:
        items, total = await self.service.list_items(limit, offset)
        return ItemListResponse(
            items=[ItemResponse.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_item(self, item_id: int) -> ItemResponse:
        return ItemResponse.model_validate(await self.service.get_item(item_id))

    async def create_item(self, request: ItemCreateRequest) -> ItemResponse:
        item = await self.service.create_item(request.name, request.description)
        return ItemResponse.model_validate(item)

    async def update_item(self, item_id: int, request: ItemUpdateRequest) -> ItemResponse:
        changes = request.model_dump(exclude_unset=True)
        # name is NOT NULL; an explicit null means "leave unchanged"
        if changes.get("name", "") is None:
            del changes["name"]
        item = await self.service.update_item(item_id, changes)
        return ItemResponse.model_validate(item)

    async def delete_item(self, item_id: int) -> None:
        await self.service.delete_item(item_id)
