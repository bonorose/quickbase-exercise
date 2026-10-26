#!/usr/bin/env python3
# ******************************************************************************
# * @file    __init__.py
# * @author  Simeon Marlokov
# * @brief   Import every model so Base.metadata is complete for Alembic.
# * @date    25.10.2026
# ******************************************************************************
from src.models.audit_event import AuditEvent
from src.models.base import Base
from src.models.chat_message import ChatMessage
from src.models.chat_session import ChatSession
from src.models.discussion import Discussion
from src.models.organization import Organization
from src.models.pending_revision import PendingRevision
from src.models.revision import Revision
from src.models.revoked_token import RevokedToken
from src.models.ticket import Ticket
from src.models.user import User

__all__ = [
    "AuditEvent",
    "Base",
    "ChatMessage",
    "ChatSession",
    "Discussion",
    "Organization",
    "PendingRevision",
    "RevokedToken",
    "Revision",
    "Ticket",
    "User",
]
