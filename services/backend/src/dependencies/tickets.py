#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/tickets.py
# * @author  Simeon Marlokov
# * @brief   Ticket wiring: session + organization -> repositories -> service -> controller
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends

from src.controllers.ticket_controller import TicketController
from src.dependencies.database import SessionDep
from src.dependencies.organizations import OrganizationDep
from src.repositories.discussion_repository import DiscussionRepository
from src.repositories.revision_repository import RevisionRepository
from src.repositories.ticket_repository import TicketRepository
from src.services.pending_revision_service import build_pending_revision_service
from src.services.ticket_service import TicketService


def get_ticket_controller(session: SessionDep, organization: OrganizationDep) -> TicketController:
    service = TicketService(
        TicketRepository(session, organization),
        RevisionRepository(session, organization),
        DiscussionRepository(session, organization),
    )
    return TicketController(service, build_pending_revision_service(session, organization))


TicketControllerDep = Annotated[TicketController, Depends(get_ticket_controller)]
