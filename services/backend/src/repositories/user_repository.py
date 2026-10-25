#!/usr/bin/env python3
# ******************************************************************************
# * @file    user_repository.py
# * @author  Simeon Marlokov
# * @brief   User data access
# * @date    25.10.2026
# ******************************************************************************
from sqlalchemy import func, select

from src.models.user import User
from src.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(func.lower(User.email) == email.lower()))
