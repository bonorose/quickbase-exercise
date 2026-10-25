#!/usr/bin/env python3
# ******************************************************************************
# * @file    main.py
# * @author  Simeon Marlokov
# * @brief   FastAPI application entrypoint
# * @date    25.10.2026
# ******************************************************************************
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.core.config import get_settings
from src.core.exceptions import DomainError, UnauthorizedError
from src.core.logging import setup_logging
from src.core.openapi import install_openapi
from src.db.session import engine
from src.middlewares.auth import AuthMiddleware
from src.routers import PUBLIC_API_ROUTES, api_router, health

settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")
    yield
    await engine.dispose()


public_routes = frozenset((method, settings.api_v1_prefix + path) for method, path in PUBLIC_API_ROUTES)

app = FastAPI(title=settings.app_name, lifespan=lifespan)
install_openapi(app, public_routes)

# Last added = outermost: CORS must wrap auth so 401 responses still carry CORS headers
app.add_middleware(AuthMiddleware, fastapi_app=app, public_routes=public_routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, UnauthorizedError) else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)


app.include_router(health.router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
