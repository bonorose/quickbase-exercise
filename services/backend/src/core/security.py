#!/usr/bin/env python3
# ******************************************************************************
# * @file    security.py
# * @author  Simeon Marlokov
# * @brief   Password hashing and JWT helpers
# * @date    25.10.2026
# ******************************************************************************
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import bcrypt
import jwt

from src.core.config import get_settings

ROLES = frozenset({"operator", "team_lead"})


@dataclass(frozen=True)
class TokenClaims:
    sub: int
    organization_id: int
    role: str
    jti: str
    exp: int


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user) -> tuple[str, int]:
    """Sign a token from the user row. ``jti`` is the revocation id."""
    settings = get_settings()
    expires_in = settings.jwt_expire_minutes * 60
    expire_at = datetime.now(UTC) + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user.id),
        "organization_id": user.organization_id,
        "role": user.role,
        "jti": uuid4().hex,
        "exp": expire_at,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> TokenClaims | None:
    """Return the claims, or None when the token is invalid, expired, or missing a claim."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    try:
        role = payload["role"]
        jti = payload["jti"]
        claims = TokenClaims(
            sub=int(payload["sub"]),
            organization_id=int(payload["organization_id"]),
            role=role,
            jti=jti,
            exp=int(payload["exp"]),
        )
    except (KeyError, TypeError, ValueError):
        return None
    if claims.role not in ROLES or not isinstance(jti, str) or not jti:
        return None
    return claims
