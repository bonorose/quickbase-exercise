#!/usr/bin/env python3
# ******************************************************************************
# * @file    organization.py
# * @author  Simeon Marlokov
# * @brief   Organization (team) ORM model. The tenant boundary.
# * @date    25.10.2026
# ******************************************************************************
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
