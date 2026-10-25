#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/health.py
# * @author  Simeon Marlokov
# * @brief   Health wiring: session -> HealthRepository -> HealthService -> HealthController
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends

from src.controllers.health_controller import HealthController
from src.dependencies.database import SessionDep
from src.repositories.health_repository import HealthRepository
from src.services.health_service import HealthService


def get_health_controller(session: SessionDep) -> HealthController:
    return HealthController(HealthService(HealthRepository(session)))


HealthControllerDep = Annotated[HealthController, Depends(get_health_controller)]
