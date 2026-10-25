#!/usr/bin/env python3
# ******************************************************************************
# * @file    item.py
# * @author  Simeon Marlokov
# * @brief   Item ORM model (table defined in db/init/01_schema.sql)
# * @date    25.10.2026
# ******************************************************************************
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, FetchedValue, Identity, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Maintained by the items_set_updated_at trigger
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), server_onupdate=FetchedValue())
