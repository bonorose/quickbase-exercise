#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth.py
# * @author  Simeon Marlokov
# * @brief   Auth routes
# * @date    25.10.2026
# ******************************************************************************
from fastapi import APIRouter, status

from src.dependencies.auth import AuthControllerDep, CurrentUserDep
from src.schemas.auth.request import LoginRequest
from src.schemas.auth.response import TokenResponse, UserResponse
from src.schemas.common.response import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])

UNAUTHORIZED = {status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}}


@router.post("/login", response_model=TokenResponse, responses=UNAUTHORIZED)
async def login(request: LoginRequest, controller: AuthControllerDep):
    return await controller.login(request)


@router.get("/me", response_model=UserResponse, responses=UNAUTHORIZED)
async def me(user: CurrentUserDep, controller: AuthControllerDep):
    return controller.me(user)
