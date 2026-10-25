#!/usr/bin/env python3
# ******************************************************************************
# * @file    user.py
# * @author  Simeon Marlokov
# * @brief   User ORM model (table defined in db/init/01_schema.sql)
# * @date    25.10.2026
# ******************************************************************************
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
