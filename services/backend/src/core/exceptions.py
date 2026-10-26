#!/usr/bin/env python3
# ******************************************************************************
# * @file    exceptions.py
# * @author  Simeon Marlokov
# * @brief   Domain exceptions raised by services, mapped to HTTP in main.py
# * @date    25.10.2026
# ******************************************************************************


class DomainError(Exception):
    status_code: int = 400

    def __init__(self, message: str, **extra: object):
        super().__init__(message)
        self.message = message
        self.extra = extra


class NotFoundError(DomainError):
    """Missing row, including another organization's row.

    Organization-scoped repositories return None for a foreign id. Services turn that into
    this error so the caller sees 404, never 403.
    """

    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class ForbiddenError(DomainError):
    status_code = 403


class GoneError(DomainError):
    status_code = 410


class UnauthorizedError(DomainError):
    status_code = 401


class RateLimitError(DomainError):
    status_code = 429

    def __init__(self, retry_after: int):
        super().__init__("Too many requests")
        self.retry_after = max(1, int(retry_after))


class ServiceUnavailableError(DomainError):
    status_code = 503
