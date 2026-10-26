#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/audit.py
# * @author  Simeon Marlokov
# * @brief   Audit wiring.
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends

from src.controllers.audit_controller import AuditController
from src.dependencies.database import SessionDep
from src.dependencies.organizations import OrganizationDep
from src.repositories.audit_repository import AuditRepository
from src.repositories.ticket_repository import TicketRepository
from src.services.audit_service import AuditService


def get_audit_controller(session: SessionDep, organization: OrganizationDep) -> AuditController:
    return AuditController(
        AuditService(AuditRepository(session, organization), TicketRepository(session, organization), organization)
    )


AuditControllerDep = Annotated[AuditController, Depends(get_audit_controller)]
