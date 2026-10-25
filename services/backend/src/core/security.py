#!/usr/bin/env python3
# ******************************************************************************
# * @file    security.py
# * @author  Simeon Marlokov
# * @brief   Password hashing and JWT helpers
# * @date    25.10.2026
# ******************************************************************************
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from src.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(subject: str) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.jwt_expire_minutes * 60
    payload = {"sub": subject, "exp": datetime.now(UTC) + timedelta(seconds=expires_in)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm), expires_in


def decode_access_token(token: str) -> str | None:
    """Returns the token subject, or None when the token is invalid or expired."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")
