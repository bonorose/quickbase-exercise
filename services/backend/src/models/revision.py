#!/usr/bin/env python3
# ******************************************************************************
# * @file    revision.py
# * @author  Simeon Marlokov
# * @brief   Immutable ticket revision. Written when a pending revision is approved.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, ForeignKeyConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.user import User


class Revision(Base):
    __tablename__ = "revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "ticket_id"],
            ["tickets.organization_id", "tickets.id"],
            name="fk_revisions_ticket_organization",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[int] = mapped_column(BigInteger)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", name="fk_revisions_organization_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", name="fk_revisions_user_id"))
    initial_contents: Mapped[dict[str, Any]] = mapped_column(JSONB)
    changed_contents: Mapped[dict[str, Any]] = mapped_column(JSONB)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()
