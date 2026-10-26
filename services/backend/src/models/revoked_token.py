#!/usr/bin/env python3
# ******************************************************************************
# * @file    revoked_token.py
# * @author  Simeon Marlokov
# * @brief   Global jti denylist. Not organization-scoped.
# * @date    26.10.2026
# ******************************************************************************
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
