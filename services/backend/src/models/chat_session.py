#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat_session.py
# * @author  Simeon Marlokov
# * @brief   Owner-private chat session. Team leads do not read each other's chats.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, desc, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="chat_sessions_organization_id_id_key"),
        Index("chat_sessions_owner_activity_idx", "organization_id", "user_id", desc("last_activity_at")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", name="fk_chat_sessions_organization_id")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", name="fk_chat_sessions_user_id"))
    title: Mapped[str] = mapped_column(String(120))
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
