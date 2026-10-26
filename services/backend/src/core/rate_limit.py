#!/usr/bin/env python3
# ******************************************************************************
# * @file    rate_limit.py
# * @author  Simeon Marlokov
# * @brief   In-process sliding window. A Redis implementation can share the same calls.
# * @date    26.10.2026
# ******************************************************************************
import time
from typing import Protocol

from src.core.config import get_settings
from src.core.exceptions import RateLimitError
from src.core.organization import OrganizationContext


class RateLimiter(Protocol):
    def allow(self, key: str, *, limit: int, window_seconds: float, now: float | None = None) -> int | None:
        """Record one hit. Return Retry-After seconds when the window is full."""


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}

    def reset(self) -> None:
        self._hits.clear()

    def allow(self, key: str, *, limit: int, window_seconds: float, now: float | None = None) -> int | None:
        moment = time.monotonic() if now is None else now
        hits = [stamp for stamp in self._hits.get(key, []) if moment - stamp < window_seconds]
        if len(hits) >= limit:
            self._hits[key] = hits
            oldest = hits[0] if hits else moment
            return max(1, int(window_seconds - (moment - oldest)) + 1)
        hits.append(moment)
        self._hits[key] = hits
        return None


_limiter = MemoryRateLimiter()


def get_rate_limiter() -> MemoryRateLimiter:
    return _limiter


def client_ip(peer: str | None, forwarded_for: str | None) -> str:
    """Use X-Forwarded-For only when the immediate peer is a configured trusted proxy."""
    host = peer or "unknown"
    trusted = {item.strip() for item in get_settings().trusted_proxies.split(",") if item.strip()}
    if trusted and host in trusted and forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return host


def enforce_login_limit(ip: str, email: str) -> None:
    settings = get_settings()
    limiter = get_rate_limiter()
    retry = limiter.allow(
        f"login:{ip}:{email.strip().lower()}",
        limit=settings.rate_limit_login_email,
        window_seconds=settings.rate_limit_login_email_window_seconds,
    )
    if retry is None:
        retry = limiter.allow(
            f"login-ip:{ip}",
            limit=settings.rate_limit_login_ip,
            window_seconds=settings.rate_limit_login_ip_window_seconds,
        )
    if retry is not None:
        raise RateLimitError(retry)


def enforce_write_limit(organization: OrganizationContext) -> None:
    """Shared budget for chat sends and approve. Checked before any model call."""
    settings = get_settings()
    limiter = get_rate_limiter()
    retry = limiter.allow(
        f"write-user:{organization.user_id}",
        limit=settings.rate_limit_user_per_minute,
        window_seconds=60,
    )
    if retry is None:
        retry = limiter.allow(
            f"write-org:{organization.organization_id}",
            limit=settings.rate_limit_organization_per_minute,
            window_seconds=60,
        )
    if retry is not None:
        raise RateLimitError(retry)
