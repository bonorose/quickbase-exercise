#!/usr/bin/env python3
# ******************************************************************************
# * @file    discussion.py
# * @author  Simeon Marlokov
# * @brief   Staff comment on a ticket. Read-only for the agent and untrusted.
# * @date    25.10.2026
# ******************************************************************************
from sqlalchemy import BigInteger, ForeignKey, ForeignKeyConstraint, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.user import User


class Discussion(Base):
    __tablename__ = "discussions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "ticket_id"],
            ["tickets.organization_id", "tickets.id"],
            name="fk_discussions_ticket_organization",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    ticket_id: Mapped[int] = mapped_column(BigInteger)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", name="fk_discussions_organization_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", name="fk_discussions_user_id"))
    contents: Mapped[str] = mapped_column(Text)

    user: Mapped[User] = relationship()
