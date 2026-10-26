#!/usr/bin/env python3
# ******************************************************************************
# * @file    middlewares/auth.py
# * @author  Simeon Marlokov
# * @brief   Authentication middleware. Bearer or the httpOnly session cookie.
# *          Cookie-authenticated unsafe methods must echo the CSRF cookie.
# * @date    26.10.2026
# ******************************************************************************
import hmac

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.cookies import CSRF_COOKIE, SESSION_COOKIE
from src.core.exceptions import UnauthorizedError
from src.core.organization import OrganizationContext
from src.db.session import get_session_factory
from src.repositories.organization_repository import OrganizationRepository
from src.repositories.revoked_token_repository import RevokedTokenRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService

_UNSAFE = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _unauthorized(message: str) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": message}, headers={"WWW-Authenticate": "Bearer"})


def _csrf_failed() -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": "CSRF check failed"})


def _internal_error() -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, fastapi_app: FastAPI, public_routes: frozenset[tuple[str, str]]):
        super().__init__(app)
        self.public_routes = public_routes
        # API docs are tooling, not API operations
        self.docs_paths = {
            fastapi_app.docs_url,
            fastapi_app.redoc_url,
            fastapi_app.openapi_url,
            fastapi_app.swagger_ui_oauth2_redirect_url,
        } - {None}

    def _is_public(self, request: Request) -> bool:
        path = request.url.path
        return path in self.docs_paths or (request.method, path) in self.public_routes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # CORS preflights carry no credentials
        if request.method == "OPTIONS" or self._is_public(request):
            return await call_next(request)

        bearer = _bearer(request)
        cookie = request.cookies.get(SESSION_COOKIE)
        if bearer:
            token = bearer
            via_cookie = False
        elif cookie:
            token = cookie
            via_cookie = True
        else:
            return _unauthorized("Not authenticated")

        if via_cookie and request.method in _UNSAFE and not _csrf_ok(request):
            return _csrf_failed()

        try:
            async with get_session_factory()() as session:
                session.info["organization_id"] = None
                user, claims = await AuthService(
                    UserRepository(session),
                    OrganizationRepository(session),
                    RevokedTokenRepository(session),
                ).get_user_from_token(token)
        except UnauthorizedError as exc:
            return _unauthorized(exc.message)
        except Exception:
            logger.exception("Auth infrastructure failed")
            return _internal_error()

        if claims.organization_id != user.organization_id:
            return _unauthorized("Invalid or expired token")
        request.state.user = user
        request.state.claims = claims
        request.state.organization = OrganizationContext(
            organization_id=user.organization_id,
            user_id=user.id,
            role=user.role,
        )
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled request error")
            return _internal_error()


def _bearer(request: Request) -> str | None:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() == "bearer" and token:
        return token
    return None


def _csrf_ok(request: Request) -> bool:
    header = request.headers.get("x-csrf-token") or ""
    cookie = request.cookies.get(CSRF_COOKIE) or ""
    if not header or not cookie:
        return False
    return hmac.compare_digest(header, cookie)
