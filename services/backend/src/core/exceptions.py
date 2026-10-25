#!/usr/bin/env python3
# ******************************************************************************
# * @file    exceptions.py
# * @author  Simeon Marlokov
# * @brief   Domain exceptions raised by services, mapped to HTTP in main.py
# * @date    25.10.2026
# ******************************************************************************


class DomainError(Exception):
    status_code: int = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class UnauthorizedError(DomainError):
    status_code = 401
