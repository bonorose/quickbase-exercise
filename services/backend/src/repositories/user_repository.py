#!/usr/bin/env python3
# ******************************************************************************
# * @file    user_repository.py
# * @author  Simeon Marlokov
# * @brief   User data access. Login lookups go through SECURITY DEFINER functions
# *          because the request has no organization yet and users are under RLS.
# * @date    25.10.2026
# ******************************************************************************
from sqlalchemy import select, text

from src.models.user import User
from src.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def find_for_login(self, email: str) -> User | None:
        statement = select(User).from_statement(text("SELECT * FROM auth_find_user(:email)"))
        return await self.session.scalar(statement, {"email": email})

    async def find_for_auth(self, user_id: int) -> User | None:
        statement = select(User).from_statement(text("SELECT * FROM auth_get_user(:id)"))
        return await self.session.scalar(statement, {"id": user_id})
