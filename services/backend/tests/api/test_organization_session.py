import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from tests.factories import commit_operator

from src.core.config import get_settings

pytestmark = pytest.mark.api


async def test_organization_setting_survives_commit_and_does_not_leak(owner_engine):
    first, _ = await commit_operator(owner_engine, email="a@excellence.qai.local", organization_name="Excellence")
    # Second organization needs its own committed row. commit_operator always creates a new organization
    # with the given name, so use a second name and then read both ids from the result.
    second, _ = await commit_operator(
        owner_engine,
        email="b@quantum.qai.local",
        organization_name="Quantum Workflow",
    )
    engine = create_async_engine(get_settings().database_url, pool_size=1, max_overflow=0)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            session.info["organization_id"] = first
            seen = await session.scalar(text("SELECT current_setting('app.organization_id', true)"))
            await session.commit()
            seen_again = await session.scalar(text("SELECT current_setting('app.organization_id', true)"))
            assert seen == seen_again == str(first)
        async with factory() as session:
            session.info["organization_id"] = second
            seen = await session.scalar(text("SELECT current_setting('app.organization_id', true)"))
            assert seen == str(second)
        async with factory() as session:
            session.info["organization_id"] = None
            seen = await session.scalar(text("SELECT current_setting('app.organization_id', true)"))
            assert seen == ""
    finally:
        await engine.dispose()
