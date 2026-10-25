#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/auth.py
# * @author  Simeon Marlokov
# * @brief   Auth wiring: session -> UserRepository -> AuthService -> AuthController
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends, Request

from src.controllers.auth_controller import AuthController
from src.core.exceptions import UnauthorizedError
from src.dependencies.database import SessionDep
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService


def get_auth_controller(session: SessionDep) -> AuthController:
    return AuthController(AuthService(UserRepository(session)))


AuthControllerDep = Annotated[AuthController, Depends(get_auth_controller)]


def get_current_user(request: Request) -> User:
    """The user resolved by middlewares/auth.py. Absent only on routes marked @public."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise UnauthorizedError("Not authenticated")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
