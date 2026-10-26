"""Pytest fixtures. ``pytest -m unit`` does not start PostgreSQL."""

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(BACKEND_ROOT))

TEST_SECRET = "test-secret"
APP_PASSWORD = "qai-app-test-password"


def _unit_only(config: pytest.Config) -> bool:
    return (config.option.markexpr or "").strip() == "unit"


def _clear_settings() -> None:
    from src.core.config import get_settings
    from src.integrations.llm import get_llm_client

    get_settings.cache_clear()
    get_llm_client.cache_clear()


def _clear_caches() -> None:
    from src.db.session import get_engine, get_session_factory

    _clear_settings()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def _base_env() -> None:
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["JWT_SECRET_KEY"] = TEST_SECRET
    os.environ["JWT_EXPIRE_MINUTES"] = "60"
    os.environ["APP_ENV"] = "local"
    os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
    os.environ["SEED_USER_PASSWORD"] = "admin123"
    os.environ["POSTGRES_APP_USER"] = "qai_app"
    os.environ["POSTGRES_APP_PASSWORD"] = APP_PASSWORD
    os.environ.setdefault("POSTGRES_USER", "quickbase")
    os.environ.setdefault("POSTGRES_PASSWORD", "quickbase")
    os.environ.setdefault("POSTGRES_DB", "quickbase")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")


@pytest.fixture(autouse=True)
def _isolate_llm_and_jwt() -> None:
    """Host ``.env`` must not leak a Gemini key or a different JWT secret into tests."""
    _base_env()
    _clear_settings()
    from src.core.rate_limit import get_rate_limiter
    from src.core.revocation import clear_revocation_cache

    get_rate_limiter().reset()
    clear_revocation_cache()


@pytest.fixture(scope="session")
def migrated_database(request: pytest.FixtureRequest):
    _base_env()
    if _unit_only(request.config):
        _clear_caches()
        yield
        return

    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        "postgres:17-alpine", username="quickbase", password="quickbase", dbname="quickbase"
    ) as postgres:
        os.environ["POSTGRES_USER"] = postgres.username
        os.environ["POSTGRES_PASSWORD"] = postgres.password
        os.environ["POSTGRES_DB"] = postgres.dbname
        os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
        _base_env()
        _clear_caches()
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=BACKEND_ROOT,
            check=True,
            env=os.environ.copy(),
        )
        _clear_caches()
        yield


@pytest.fixture(scope="session")
def app(migrated_database):
    _clear_caches()
    from src.main import app as fastapi_app

    @fastapi_app.get("/api/v1/__boom")
    async def boom() -> None:
        raise RuntimeError("secret boom text")

    return fastapi_app


@pytest.fixture(scope="session")
async def owner_engine(migrated_database, request: pytest.FixtureRequest) -> AsyncIterator[AsyncEngine | None]:
    if _unit_only(request.config):
        yield None
        return
    from src.core.config import get_settings

    engine = create_async_engine(get_settings().migration_database_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(owner_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Outer transaction rolled back after the test, so repository commits stay isolated."""
    async with owner_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def client(app, migrated_database):
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture(autouse=True)
async def _truncate_after_api_test(request: pytest.FixtureRequest, migrated_database):
    yield
    if request.node.get_closest_marker("api") is None or _unit_only(request.config):
        return
    from src.core.config import get_settings

    engine = create_async_engine(get_settings().migration_database_url)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE TABLE revoked_tokens, audit_events, pending_revisions, chat_messages, chat_sessions, "
                    "discussions, revisions, tickets, users, organizations RESTART IDENTITY CASCADE"
                )
            )
    finally:
        await engine.dispose()
