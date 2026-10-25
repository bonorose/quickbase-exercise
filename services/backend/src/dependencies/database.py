#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/database.py
# * @author  Simeon Marlokov
# * @brief   Per-request database session dependency
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
