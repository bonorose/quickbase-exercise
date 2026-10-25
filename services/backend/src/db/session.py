#!/usr/bin/env python3
# ******************************************************************************
# * @file    session.py
# * @author  Simeon Marlokov
# * @brief   Async SQLAlchemy engine and per-request session
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
