#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth_controller.py
# * @author  Simeon Marlokov
# * @brief   Auth controller
# * @date    25.10.2026
# ******************************************************************************
from src.models.user import User
from src.schemas.auth.request import LoginRequest
from src.schemas.auth.response import TokenResponse, UserResponse
from src.services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService):
        self.service = service

    async def login(self, request: LoginRequest) -> TokenResponse:
        token, expires_in = await self.service.login(request.email, request.password)
        return TokenResponse(access_token=token, expires_in=expires_in)

    @staticmethod
    def me(user: User) -> UserResponse:
        return UserResponse.model_validate(user)
