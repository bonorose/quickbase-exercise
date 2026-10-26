#!/usr/bin/env python3
# ******************************************************************************
# * @file    revoked_token_repository.py
# * @author  Simeon Marlokov
# * @brief   Insert, lookup and purge of revoked jti values.
# * @date    26.10.2026
# ******************************************************************************
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.revoked_token import RevokedToken


class RevokedTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        existing = await self.session.get(RevokedToken, jti)
        if existing is None:
            self.session.add(RevokedToken(jti=jti, expires_at=expires_at))

    async def is_revoked(self, jti: str) -> bool:
        row = await self.session.scalar(select(RevokedToken.jti).where(RevokedToken.jti == jti))
        return row is not None

    async def purge_expired(self, now: datetime | None = None) -> None:
        moment = now or datetime.now(UTC)
        await self.session.execute(delete(RevokedToken).where(RevokedToken.expires_at < moment))
