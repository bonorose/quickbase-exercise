#!/usr/bin/env python3
# ******************************************************************************
# * @file    pending_revision.py
# * @author  Simeon Marlokov
# * @brief   One draft of a ticket change. Approve is the only path that writes
# *          the ticket or a revision.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.user import User


class PendingRevision(Base):
    __tablename__ = "pending_revisions"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="pending_revisions_organization_id_id_key"),
        CheckConstraint("action IN ('update', 'delete')", name="pending_revisions_action_check"),
        CheckConstraint(
            "status IN ('open', 'executed', 'rejected', 'expired')",
            name="pending_revisions_status_check",
        ),
        CheckConstraint("origin IN ('human', 'agent')", name="pending_revisions_origin_check"),
        ForeignKeyConstraint(
            ["organization_id", "ticket_id"],
            ["tickets.organization_id", "tickets.id"],
            name="fk_pending_revisions_ticket_organization",
        ),
        ForeignKeyConstraint(
            ["organization_id", "session_id"],
            ["chat_sessions.organization_id", "chat_sessions.id"],
            name="fk_pending_revisions_session",
        ),
        Index(
            "pending_revisions_one_open_idx",
            "ticket_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[int] = mapped_column(BigInteger)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", name="fk_pending_revisions_organization_id")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", name="fk_pending_revisions_user_id"))
    previous_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("revisions.id", name="fk_pending_revisions_previous_revision")
    )
    changed_contents: Mapped[dict[str, Any]] = mapped_column(JSONB)
    action: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    tainted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", name="fk_pending_revisions_decided_by"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    origin: Mapped[str] = mapped_column(String(16))
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User] = relationship(foreign_keys=[user_id])
    decider: Mapped[User | None] = relationship(foreign_keys=[decided_by])
