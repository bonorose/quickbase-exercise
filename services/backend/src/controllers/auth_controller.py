#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth_controller.py
# * @author  Simeon Marlokov
# * @brief   Auth controller
# * @date    25.10.2026
# ******************************************************************************
from src.core.security import TokenClaims
from src.models.user import User
from src.schemas.auth.request import LoginRequest
from src.schemas.auth.response import OrganizationResponse, TokenResponse, UserResponse
from src.services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService):
        self.service = service

    async def login(self, request: LoginRequest) -> TokenResponse:
        token, expires_in = await self.service.login(request.email, request.password)
        return TokenResponse(access_token=token, expires_in=expires_in)

    async def logout(self, user: User, claims: TokenClaims) -> None:
        await self.service.logout(user, claims)

    async def me(self, user: User) -> UserResponse:
        user, organization = await self.service.get_profile(user)
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            organization=OrganizationResponse(id=organization.id, name=organization.name),
        )
