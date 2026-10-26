import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from tests.factories import commit_operator, hash_fast, make_organization, make_user

from src.core.config import get_settings
from src.core.exceptions import ConflictError
from src.repositories.user_repository import UserRepository

pytestmark = pytest.mark.api


async def test_email_unique_ignores_case(db_session: AsyncSession):
    organization = await make_organization(db_session)
    await make_user(db_session, organization, email="A@x.io")
    repository = UserRepository(db_session)
    with pytest.raises(ConflictError):
        await repository.create(
            email="a@x.io",
            password_hash=hash_fast("x"),
            name="Other",
            organization_id=organization.id,
            role="operator",
            is_active=True,
        )


async def test_unknown_role_is_rejected(db_session: AsyncSession):
    organization = await make_organization(db_session)
    repository = UserRepository(db_session)
    with pytest.raises(IntegrityError):
        await repository.create(
            email="admin@x.io",
            password_hash=hash_fast("x"),
            name="Admin",
            organization_id=organization.id,
            role="admin",
            is_active=True,
        )


async def test_scoped_get_hides_the_other_organization(db_session: AsyncSession):
    from tests.factories import make_ticket

    from src.core.organization import OrganizationContext
    from src.repositories.ticket_repository import TicketRepository

    excellence = await make_organization(db_session, "Excellence")
    quantum = await make_organization(db_session, "Quantum Workflow")
    foreign = await make_ticket(db_session, quantum, title="Quantum only")
    repository = TicketRepository(db_session, OrganizationContext(excellence.id, 1, "operator"))
    assert await repository.get_by_id(foreign.id) is None


async def test_concurrent_email_creates_one_winner(owner_engine):
    organization_id, _ = await commit_operator(owner_engine)
    engine = create_async_engine(get_settings().migration_database_url, poolclass=NullPool)
    password_hash = hash_fast("x")

    async def attempt() -> str:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            try:
                await UserRepository(session).create(
                    email="Race@x.io",
                    password_hash=password_hash,
                    name="Racer",
                    organization_id=organization_id,
                    role="operator",
                    is_active=True,
                )
            except ConflictError:
                return "conflict"
            return "created"

    try:
        results = await asyncio.gather(*(attempt() for _ in range(10)))
    finally:
        await engine.dispose()
    assert results.count("created") == 1
    assert results.count("conflict") == 9
    async with owner_engine.connect() as connection:
        count = await connection.scalar(text("SELECT count(*) FROM users WHERE lower(email) = 'race@x.io'"))
    assert count == 1
