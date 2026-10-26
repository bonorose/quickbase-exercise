from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.factories import commit_operator, make_discussion, make_organization, make_ticket, make_user
from tests.helpers.auth import auth_header

from src.models.revision import Revision

pytestmark = pytest.mark.api


async def _two_teams(owner_engine):
    factory = async_sessionmaker(owner_engine, expire_on_commit=False)
    async with factory() as session:
        excellence = await make_organization(session, "Excellence")
        quantum = await make_organization(session, "Quantum Workflow")
        operator = await make_user(session, excellence, email="op1@excellence.qai.local", name="Operator One")
        quantum_user = await make_user(session, quantum, email="op1@quantum.qai.local", name="Quantum Op")
        open_ticket = await make_ticket(
            session,
            excellence,
            title="Billing export fails",
            status=1,
            priority=4,
            description="Summary of billing.",
            contents="Please look at the export.",
            updated_by=operator.id,
        )
        await make_ticket(session, excellence, title="Closed VPN", status=3, priority=1, description="Done.")
        deleted = await make_ticket(
            session,
            excellence,
            title="Deleted billing",
            date_deleted=datetime.now(UTC),
        )
        foreign = await make_ticket(session, quantum, title="Quantum only secret", description="Quantum internal.")
        for index, contents in enumerate(("first", "second", "third", "fourth"), start=1):
            await make_discussion(session, open_ticket, operator, contents=f"{index}-{contents}")
        await make_discussion(session, foreign, quantum_user, contents="quantum private note")
        snapshot = {
            "title": "Billing export fails",
            "contents": "Please look at the export.",
            "status": "open",
            "priority": "high",
        }
        session.add(
            Revision(
                ticket_id=open_ticket.id,
                organization_id=excellence.id,
                user_id=operator.id,
                initial_contents=snapshot,
                changed_contents=snapshot,
            )
        )
        await session.commit()
        return open_ticket.id, deleted.id, foreign.id


async def test_list_and_detail_are_organization_scoped(client, owner_engine):
    ticket_id, deleted_id, foreign_id = await _two_teams(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")

    listed = await client.get("/api/v1/tickets", headers=headers, params={"q": "billing", "status": "open"})
    assert listed.status_code == 200
    body = listed.json()
    assert body["limit"] == 20
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Billing export fails"
    assert body["items"][0]["status"] == "open"
    assert body["items"][0]["priority"] == "high"
    assert isinstance(body["items"][0]["date_updated"], int)

    foreign_search = await client.get("/api/v1/tickets", headers=headers, params={"q": "Quantum only secret"})
    assert foreign_search.json()["items"] == []

    detail = await client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
    assert detail.status_code == 200
    ticket = detail.json()
    assert ticket["updated_by"] == {"id": ticket["updated_by"]["id"], "name": "Operator One"}
    assert [item["contents"] for item in ticket["discussions"]] == ["1-first", "2-second", "3-third", "4-fourth"]
    assert ticket["discussions"][0]["user"]["name"] == "Operator One"
    assert ticket["revisions"][0]["user"]["name"] == "Operator One"
    assert ticket["open_pending_revision"] is None
    assert "quantum private note" not in str(ticket)

    missing = await client.get("/api/v1/tickets/999999", headers=headers)
    foreign = await client.get(f"/api/v1/tickets/{foreign_id}", headers=headers)
    deleted = await client.get(f"/api/v1/tickets/{deleted_id}", headers=headers)
    assert missing.status_code == foreign.status_code == deleted.status_code == 404
    assert missing.json() == {"detail": "Ticket 999999 not found"}
    assert foreign.json() == {"detail": f"Ticket {foreign_id} not found"}
    assert deleted.json() == {"detail": f"Ticket {deleted_id} not found"}


async def test_list_validation_sort_and_openapi_lock(client, owner_engine):
    await commit_operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    assert (await client.get("/api/v1/tickets", headers=headers, params={"limit": 101})).status_code == 422
    assert (await client.get("/api/v1/tickets", headers=headers, params={"sort": "number"})).status_code == 422
    assert (await client.get("/api/v1/tickets", headers=headers, params={"status": "pending"})).status_code == 422

    schema = (await client.get("/openapi.json")).json()
    assert schema["paths"]["/api/v1/auth/login"]["post"]["security"] == []
    for path in ("/api/v1/tickets", "/api/v1/tickets/{ticket_id}"):
        operation = schema["paths"][path]["get"]
        assert operation.get("security", schema["security"]) != []


async def test_pagination_and_priority_sort(client, owner_engine):
    factory = async_sessionmaker(owner_engine, expire_on_commit=False)
    async with factory() as session:
        organization = await make_organization(session, "Excellence")
        await make_user(session, organization, email="op1@excellence.qai.local")
        await make_ticket(session, organization, title="Low", priority=2, status=1)
        await make_ticket(session, organization, title="Critical", priority=5, status=1)
        await make_ticket(session, organization, title="Lowest", priority=1, status=2)
        await session.commit()
    headers = await auth_header(client, "op1@excellence.qai.local")
    page = await client.get(
        "/api/v1/tickets",
        headers=headers,
        params={"sort": "-priority", "limit": 1, "offset": 1},
    )
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 3
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert body["items"][0]["title"] == "Low"


async def test_trigram_index_is_used(db_session: AsyncSession):
    organization = await make_organization(db_session, "Excellence")
    await db_session.execute(
        text(
            """
            INSERT INTO tickets (
                organization_id, status, priority, title, description, contents, submitted_by
            )
            SELECT :organization_id, 1, 1, 'Ticket ' || g, 'desc', 'body', 'c@example.com'
            FROM generate_series(1, 10000) AS g
            """
        ),
        {"organization_id": organization.id},
    )
    await db_session.execute(text("UPDATE tickets SET title = 'xylophonezebra case' WHERE title = 'Ticket 1'"))
    await db_session.execute(text("SET LOCAL enable_seqscan = off"))
    plan = "\n".join(
        row[0]
        for row in (
            await db_session.execute(
                text(
                    """
                    EXPLAIN SELECT id FROM tickets
                    WHERE (title || ' ' || description || ' ' || contents) ILIKE '%xylophonezebra%'
                    """
                )
            )
        ).all()
    )
    assert "tickets_search_trgm" in plan
