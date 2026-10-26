#!/usr/bin/env python3
# ******************************************************************************
# * @file    revocation_purge.py
# * @author  Simeon Marlokov
# * @brief   Nightly deletion of expired revoked jti rows.
# * @date    26.10.2026
# ******************************************************************************
import asyncio
from datetime import UTC, datetime, timedelta

from loguru import logger

from src.db.session import bind_organization, get_session_factory
from src.repositories.revoked_token_repository import RevokedTokenRepository

PURGE_HOUR_UTC = 2


def seconds_until_utc_hour(hour: int, now: datetime | None = None) -> float:
    """Seconds until the next occurrence of ``hour``:00 UTC, at least one second."""
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    target = moment.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= moment:
        target += timedelta(days=1)
    return max((target - moment).total_seconds(), 1.0)


async def purge_expired_revocations() -> None:
    factory = get_session_factory()
    async with factory() as session:
        await bind_organization(session, None)
        await RevokedTokenRepository(session).purge_expired()
        await session.commit()


async def revocation_purge_loop(stop: asyncio.Event) -> None:
    """Purge once at startup, then every night at 02:00 UTC."""
    while not stop.is_set():
        try:
            await purge_expired_revocations()
            logger.debug("Purged expired revoked tokens")
        except Exception:
            logger.exception("Revoked-token purge failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=seconds_until_utc_hour(PURGE_HOUR_UTC))
        except TimeoutError:
            continue
