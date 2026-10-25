#!/usr/bin/env python3
# ******************************************************************************
# * @file    items.py
# * @author  Simeon Marlokov
# * @brief   Item routes
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import APIRouter, Query, status

from src.dependencies.items import ItemControllerDep
from src.schemas.common.response import ErrorResponse
from src.schemas.items.request import ItemCreateRequest, ItemUpdateRequest
from src.schemas.items.response import ItemListResponse, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}
CONFLICT = {status.HTTP_409_CONFLICT: {"model": ErrorResponse}}


@router.get("", response_model=ItemListResponse)
async def list_items(
    controller: ItemControllerDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await controller.list_items(limit, offset)


@router.get("/{item_id}", response_model=ItemResponse, responses=NOT_FOUND)
async def get_item(item_id: int, controller: ItemControllerDep):
    return await controller.get_item(item_id)


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, responses=CONFLICT)
async def create_item(request: ItemCreateRequest, controller: ItemControllerDep):
    return await controller.create_item(request)


@router.patch("/{item_id}", response_model=ItemResponse, responses=NOT_FOUND | CONFLICT)
async def update_item(item_id: int, request: ItemUpdateRequest, controller: ItemControllerDep):
    return await controller.update_item(item_id, request)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
async def delete_item(item_id: int, controller: ItemControllerDep):
    await controller.delete_item(item_id)
