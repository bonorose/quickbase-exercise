#!/usr/bin/env python3
# ******************************************************************************
# * @file    main.py
# * @author  Simeon Marlokov
# * @brief   FastAPI application entrypoint
# * @date    25.10.2026
# ******************************************************************************
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.core.config import get_settings
from src.core.exceptions import DomainError, RateLimitError, UnauthorizedError
from src.core.logging import setup_logging
from src.core.openapi import install_openapi
from src.core.revocation_purge import revocation_purge_loop
from src.db.session import get_engine
from src.integrations.llm import assert_llm_provider_allowed
from src.middlewares.auth import AuthMiddleware
from src.routers import PUBLIC_API_ROUTES, api_router, health

settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    assert_llm_provider_allowed()
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")
    stop_purge = asyncio.Event()
    purge = asyncio.create_task(revocation_purge_loop(stop_purge))
    yield
    stop_purge.set()
    purge.cancel()
    await asyncio.gather(purge, return_exceptions=True)
    await get_engine().dispose()


public_routes = frozenset(
    {(method, settings.api_v1_prefix + path) for method, path in PUBLIC_API_ROUTES} | {("GET", "/livez")}
)

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
    headers: dict[str, str] = {}
    if isinstance(exc, UnauthorizedError):
        headers["WWW-Authenticate"] = "Bearer"
    if isinstance(exc, RateLimitError):
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, **exc.extra},
        headers=headers or None,
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
