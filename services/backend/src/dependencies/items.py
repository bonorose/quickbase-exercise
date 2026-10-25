#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/items.py
# * @author  Simeon Marlokov
# * @brief   Items wiring: session -> ItemRepository -> ItemService -> ItemController
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends

from src.controllers.item_controller import ItemController
from src.dependencies.database import SessionDep
from src.repositories.item_repository import ItemRepository
from src.services.item_service import ItemService


def get_item_controller(session: SessionDep) -> ItemController:
    return ItemController(ItemService(ItemRepository(session)))


ItemControllerDep = Annotated[ItemController, Depends(get_item_controller)]
