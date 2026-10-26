#!/usr/bin/env python3
# ******************************************************************************
# * @file    cookies.py
# * @author  Simeon Marlokov
# * @brief   Session and CSRF cookies for C-14.
# * @date    26.10.2026
# ******************************************************************************
import secrets

from fastapi import Response

from src.core.config import get_settings

SESSION_COOKIE = "qb_session"
CSRF_COOKIE = "qb_csrf"


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _secure() -> bool:
    return get_settings().app_env == "production"


def set_session_cookies(response: Response, token: str, csrf: str, max_age: int) -> None:
    secure = _secure()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        max_age=max_age,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookies(response: Response) -> None:
    secure = _secure()
    response.delete_cookie(SESSION_COOKIE, path="/", secure=secure, httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=secure, httponly=False, samesite="lax")
