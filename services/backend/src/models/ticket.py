#!/usr/bin/env python3
# ******************************************************************************
# * @file    ticket.py
# * @author  Simeon Marlokov
# * @brief   Ticket ORM model. contents and description are untrusted text.
# * @date    25.10.2026
# ******************************************************************************
from datetime import datetime
from enum import IntEnum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    FetchedValue,
    ForeignKey,
    Identity,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    desc,
    func,
    literal_column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.user import User


class TicketStatus(IntEnum):
    open = 1
    blocked = 2
    closed = 3


class TicketPriority(IntEnum):
    lowest = 1
    low = 2
    medium = 3
    high = 4
    critical = 5


STATUS_NAMES = frozenset(status.name for status in TicketStatus)
PRIORITY_NAMES = frozenset(priority.name for priority in TicketPriority)
TICKET_SORTS = frozenset({"-date_updated", "date_updated", "priority", "-priority", "id"})
# Postgres stores varchar || as text casts. The model must match that or alembic check drifts.
SEARCH_DOCUMENT = "((((title::text || ' '::text) || description::text) || ' '::text) || contents::text)"


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="tickets_organization_id_id_key"),
        CheckConstraint("status IN (1, 2, 3)", name="tickets_status_check"),
        CheckConstraint("priority IN (1, 2, 3, 4, 5)", name="tickets_priority_check"),
        Index("tickets_organization_status_idx", "organization_id", "status"),
        Index("tickets_organization_date_updated_idx", "organization_id", desc("date_updated")),
        Index(
            "tickets_search_trgm",
            literal_column(SEARCH_DOCUMENT),
            postgresql_using="gin",
            postgresql_ops={SEARCH_DOCUMENT: "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", name="fk_tickets_organization_id"))
    status: Mapped[int] = mapped_column(SmallInteger)
    priority: Mapped[int] = mapped_column(SmallInteger)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(500))
    contents: Mapped[str] = mapped_column(String(2000))
    submitted_by: Mapped[str] = mapped_column(String(255))
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", name="fk_tickets_updated_by"))
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=FetchedValue(),
    )
    date_deleted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])
