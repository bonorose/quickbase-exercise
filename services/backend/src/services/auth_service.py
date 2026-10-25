#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth_service.py
# * @author  Simeon Marlokov
# * @brief   Authentication logic: credential check, token issue/resolve
# * @date    25.10.2026
# ******************************************************************************
from src.core.exceptions import UnauthorizedError
from src.core.security import create_access_token, decode_access_token, verify_password
from src.models.user import User
from src.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def login(self, email: str, password: str) -> tuple[str, int]:
        user = await self.repository.get_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        return create_access_token(str(user.id))

    async def get_user_from_token(self, token: str) -> User:
        subject = decode_access_token(token)
        user = await self.repository.get_by_id(int(subject)) if subject and subject.isdigit() else None
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid or expired token")
        return user
