#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/database.py
# * @author  Simeon Marlokov
# * @brief   Per-request database session, bound to the caller's organization
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import bind_organization, get_session_factory


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    organization = getattr(request.state, "organization", None)
    organization_id = None if organization is None else organization.organization_id
    async with get_session_factory()() as session:
        await bind_organization(session, organization_id)
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
