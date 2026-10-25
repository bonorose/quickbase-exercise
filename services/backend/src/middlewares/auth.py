#!/usr/bin/env python3
# ******************************************************************************
# * @file    middlewares/auth.py
# * @author  Simeon Marlokov
# * @brief   Authentication middleware. Every request requires a valid bearer token
# *          unless its (method, path) is in the explicit public_routes allowlist.
# * @date    25.10.2026
# ******************************************************************************
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.exceptions import UnauthorizedError
from src.db.session import SessionFactory
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService


def _unauthorized(message: str) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": message}, headers={"WWW-Authenticate": "Bearer"})


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

        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            return _unauthorized("Not authenticated")

        async with SessionFactory() as session:
            try:
                request.state.user = await AuthService(UserRepository(session)).get_user_from_token(token)
            except UnauthorizedError as exc:
                return _unauthorized(exc.message)

        return await call_next(request)
