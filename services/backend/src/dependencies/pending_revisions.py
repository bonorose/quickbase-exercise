#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/pending_revisions.py
# * @author  Simeon Marlokov
# * @brief   Pending revision wiring.
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends

from src.controllers.pending_revision_controller import PendingRevisionController
from src.dependencies.database import SessionDep
from src.dependencies.organizations import OrganizationDep
from src.services.pending_revision_service import build_pending_revision_service


def get_pending_revision_controller(session: SessionDep, organization: OrganizationDep) -> PendingRevisionController:
    return PendingRevisionController(build_pending_revision_service(session, organization))


PendingRevisionControllerDep = Annotated[PendingRevisionController, Depends(get_pending_revision_controller)]
