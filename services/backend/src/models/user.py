#!/usr/bin/env python3
# ******************************************************************************
# * @file    user.py
# * @author  Simeon Marlokov
# * @brief   User ORM model. One organization per user.
# * @date    25.10.2026
# ******************************************************************************
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", name="fk_users_organization_id"))
    role: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('operator', 'team_lead')", name="users_role_check"),
        Index("users_email_lower_key", func.lower(email), unique=True),
    )
