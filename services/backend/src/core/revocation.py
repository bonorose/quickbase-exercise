#!/usr/bin/env python3
# ******************************************************************************
# * @file    revocation.py
# * @author  Simeon Marlokov
# * @brief   Short in-process cache of jti revocation lookups.
# * @date    26.10.2026
# ******************************************************************************
import time

_TTL_SECONDS = 30.0
_cache: dict[str, tuple[bool, float]] = {}


def cached_revoked(jti: str, now: float | None = None) -> bool | None:
    moment = time.monotonic() if now is None else now
    item = _cache.get(jti)
    if item is None:
        return None
    revoked, until = item
    if moment > until:
        _cache.pop(jti, None)
        return None
    return revoked


def remember_revoked(jti: str, revoked: bool, now: float | None = None) -> None:
    moment = time.monotonic() if now is None else now
    _cache[jti] = (revoked, moment + _TTL_SECONDS)


def clear_revocation_cache() -> None:
    _cache.clear()
