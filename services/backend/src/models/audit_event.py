#!/usr/bin/env python3
# ******************************************************************************
# * @file    audit_event.py
# * @author  Simeon Marlokov
# * @brief   Append-only audit row. The application role can insert and select.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.user import User


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint("actor_type IN ('user', 'agent', 'system')", name="audit_events_actor_type_check"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", name="fk_audit_events_organization_id"))
    actor_type: Mapped[str] = mapped_column(String(16))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", name="fk_audit_events_actor_id"))
    event: Mapped[str] = mapped_column(String(64))
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    ticket_id: Mapped[int | None] = mapped_column(BigInteger)
    pending_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pending_revisions.id", name="fk_audit_events_pending_revision_id")
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    actor: Mapped[User | None] = relationship(foreign_keys=[actor_id])
