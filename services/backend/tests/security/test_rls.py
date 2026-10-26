import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker
from tests.factories import make_organization, make_ticket, make_user

from src.db.session import get_engine
from src.models.ticket import Ticket
from src.models.user import User

pytestmark = pytest.mark.api


async def test_role_cannot_bypass_rls(owner_engine):
    async with owner_engine.connect() as connection:
        row = (
            await connection.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'qai_app'"))
        ).one()
    assert row == (False, False)


async def test_every_organization_table_forces_rls(owner_engine):
    async with owner_engine.connect() as connection:
        rows = (
            await connection.execute(
                text(
                    """
                    SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public'
                      AND c.relkind = 'r'
                      AND EXISTS (
                          SELECT 1 FROM pg_attribute a
                          WHERE a.attrelid = c.oid
                            AND a.attname = 'organization_id'
                            AND NOT a.attisdropped
                      )
                    ORDER BY c.relname
                    """
                )
            )
        ).all()
        organizations = (
            await connection.execute(
                text(
                    """
                    SELECT c.relrowsecurity, c.relforcerowsecurity
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public' AND c.relname = 'organizations'
                    """
                )
            )
        ).one()
    assert {name for name, _, _ in rows} == {
        "audit_events",
        "chat_messages",
        "chat_sessions",
        "discussions",
        "pending_revisions",
        "revisions",
        "tickets",
        "users",
    }
    assert all(enabled and forced for _, enabled, forced in rows)
    assert organizations == (True, True)


async def test_rls_filters_reads_and_rejects_foreign_inserts(owner_engine):
    factory = async_sessionmaker(owner_engine, expire_on_commit=False)
    async with factory() as session:
        excellence = await make_organization(session, "Excellence")
        quantum = await make_organization(session, "Quantum Workflow")
        await make_user(session, excellence, email="a@excellence.qai.local")
        await make_user(session, quantum, email="b@quantum.qai.local")
        own = await make_ticket(session, excellence, title="Excellence ticket")
        foreign = await make_ticket(session, quantum, title="Quantum ticket")
        await session.commit()
        excellence_id = excellence.id
        quantum_id = quantum.id
        own_id = own.id
        foreign_id = foreign.id

    app_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with app_factory() as session:
        session.info["organization_id"] = excellence_id
        tickets = (await session.scalars(select(Ticket))).all()
        users = (await session.scalars(select(User))).all()
        assert {ticket.id for ticket in tickets} == {own_id}
        assert foreign_id not in {ticket.id for ticket in tickets}
        assert all(user.organization_id == excellence_id for user in users)

    async with app_factory() as session:
        session.info["organization_id"] = None
        assert (await session.scalars(select(Ticket))).all() == []

    async with app_factory() as session:
        session.info["organization_id"] = excellence_id
        session.add(
            Ticket(
                organization_id=quantum_id,
                status=1,
                priority=1,
                title="smuggled",
                description="no",
                contents="no",
                submitted_by="c@example.com",
            )
        )
        with pytest.raises(DBAPIError, match="row-level security"):
            await session.commit()
