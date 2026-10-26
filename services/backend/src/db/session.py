#!/usr/bin/env python3
# ******************************************************************************
# * @file    session.py
# * @author  Simeon Marlokov
# * @brief   Async SQLAlchemy engine and per-request session
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from src.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


def _apply_organization_setting(session: Session, _transaction, connection) -> None:
    """Transaction-local organization id for row-level security.

    Repositories commit, so a request spans several transactions. ``set_config(..., true)``
    dies with the transaction; this listener puts the id back at the start of the next one.
    An empty value fails closed (no rows) and never leaks across pooled connections.
    """
    organization_id = session.info.get("organization_id")
    value = "" if organization_id is None else str(organization_id)
    connection.execute(text("SELECT set_config('app.organization_id', :value, true)"), {"value": value})


event.listen(Session, "after_begin", _apply_organization_setting)


async def bind_organization(session: AsyncSession, organization_id: int | None) -> None:
    """Set the organization for an already-open transaction as well as later ones."""
    session.info["organization_id"] = organization_id
    await session.execute(
        text("SELECT set_config('app.organization_id', :value, true)"),
        {"value": "" if organization_id is None else str(organization_id)},
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """Placeholder replaced by dependencies.database, which knows the request.

    Kept so imports of ``get_session`` from this module still yield a session when no
    organization has been resolved (tests and scripts).
    """
    async with get_session_factory()() as session:
        await bind_organization(session, None)
        yield session
