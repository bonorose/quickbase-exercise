#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth.py
# * @author  Simeon Marlokov
# * @brief   Auth routes
# * @date    26.10.2026
# ******************************************************************************
from fastapi import APIRouter, Request, Response, status

from src.core.config import get_settings
from src.core.cookies import clear_session_cookies, new_csrf_token, set_session_cookies
from src.core.exceptions import UnauthorizedError
from src.core.rate_limit import client_ip, enforce_login_limit
from src.dependencies.auth import AuthControllerDep, CurrentUserDep
from src.schemas.auth.request import LoginRequest
from src.schemas.auth.response import TokenResponse, UserResponse
from src.schemas.common.response import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])

UNAUTHORIZED = {status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}}


@router.post("/login", response_model=TokenResponse, responses=UNAUTHORIZED)
async def login(body: LoginRequest, request: Request, response: Response, controller: AuthControllerDep):
    peer = request.client.host if request.client else None
    enforce_login_limit(client_ip(peer, request.headers.get("x-forwarded-for")), body.email)
    token = await controller.login(body)
    set_session_cookies(response, token.access_token, new_csrf_token(), token.expires_in)
    if get_settings().auth_return_token_in_body:
        return token
    return TokenResponse(access_token="", token_type="bearer", expires_in=token.expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, user: CurrentUserDep, controller: AuthControllerDep):
    claims = getattr(request.state, "claims", None)
    if claims is None:
        raise UnauthorizedError("Not authenticated")
    await controller.logout(user, claims)
    outgoing = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookies(outgoing)
    return outgoing


@router.get("/me", response_model=UserResponse, responses=UNAUTHORIZED)
async def me(user: CurrentUserDep, controller: AuthControllerDep):
    return await controller.me(user)
