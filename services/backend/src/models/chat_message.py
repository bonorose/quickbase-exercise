#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat_message.py
# * @author  Simeon Marlokov
# * @brief   One stored turn. ``content`` holds parts and the provider raw payload.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Identity, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'tool', 'system')", name="chat_messages_role_check"),
        ForeignKeyConstraint(
            ["organization_id", "session_id"],
            ["chat_sessions.organization_id", "chat_sessions.id"],
            name="fk_chat_messages_session_organization",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", name="fk_chat_messages_organization_id")
    )
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    model: Mapped[str | None] = mapped_column(String(128))
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
