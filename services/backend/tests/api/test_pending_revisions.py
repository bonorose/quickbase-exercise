import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from tests.factories import make_organization, make_ticket, make_user
from tests.fakes.llm import FakeLLMClient
from tests.helpers.auth import auth_header
from tests.helpers.sse import read_events

from src.core.config import get_settings
from src.core.organization import OrganizationContext
from src.db.session import bind_organization
from src.integrations.llm import get_llm_client
from src.integrations.llm.types import LLMMessage, TextDelta, ToolCall, TurnComplete
from src.models.revision import Revision
from src.services.pending_revision_service import build_pending_revision_service
from src.tools.base import ToolContext
from src.tools.mutate_ticket import MutateTicketTool

pytestmark = pytest.mark.api


async def _seed(owner_engine):
    factory = async_sessionmaker(owner_engine, expire_on_commit=False)
    async with factory() as session:
        excellence = await make_organization(session, "Excellence")
        quantum = await make_organization(session, "Quantum Workflow")
        operator = await make_user(session, excellence, email="op1@excellence.qai.local", name="Ada")
        colleague = await make_user(session, excellence, email="op2@excellence.qai.local", name="Bea")
        lead = await make_user(session, excellence, email="lead@excellence.qai.local", name="Cara", role="team_lead")
        outsider = await make_user(session, quantum, email="op1@quantum.qai.local", name="Quinn")
        ticket = await make_ticket(session, excellence, title="Billing export", priority=2, updated_by=operator.id)
        foreign = await make_ticket(session, quantum, title="Quantum only")
        await session.commit()
        return {
            "org": excellence.id,
            "operator": operator.id,
            "colleague": colleague.id,
            "lead": lead.id,
            "ticket": ticket.id,
            "foreign": foreign.id,
            "outsider": outsider.id,
        }


async def _revisions(owner_engine, ticket_id: int) -> int:
    async with owner_engine.connect() as connection:
        return await connection.scalar(
            select(func.count()).select_from(Revision).where(Revision.ticket_id == ticket_id)
        )


async def test_claim_save_and_approve_write_a_revision_only_on_approve(client, owner_engine):
    seeded = await _seed(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    ticket_id = seeded["ticket"]
    assert await _revisions(owner_engine, ticket_id) == 0

    claimed = await client.post(
        f"/api/v1/tickets/{ticket_id}/pending-revisions",
        headers=headers,
        json={"action": "update", "changed_contents": {"priority": "high"}},
    )
    assert claimed.status_code == 201, claimed.text
    body = claimed.json()
    assert body["origin"] == "human"
    assert body["expires_at"] is None
    assert body["tainted"] is False
    assert body["diff"]["priority"] == {"from": "low", "to": "high"}
    draft_id = body["id"]
    assert await _revisions(owner_engine, ticket_id) == 0

    detail = await client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
    assert detail.json()["open_pending_revision"]["owner"]["name"] == "Ada"
    assert detail.json()["priority"] == "low"

    smuggled = await client.post(
        f"/api/v1/tickets/{ticket_id}/pending-revisions",
        headers=headers,
        json={"action": "update", "changed_contents": {"description": "nope"}},
    )
    assert smuggled.status_code == 422

    saved = await client.put(
        f"/api/v1/pending-revisions/{draft_id}",
        headers=headers,
        json={"changed_contents": {"priority": "critical"}, "action": "update"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["expires_at"] is None
    assert saved.json()["changed_contents"]["priority"] == "critical"

    approved = await client.post(f"/api/v1/pending-revisions/{draft_id}/approve", headers=headers, json={})
    assert approved.status_code == 200, approved.text
    assert approved.json()["ticket"]["priority"] == "critical"
    assert approved.json()["pending_revision"]["status"] == "executed"
    assert await _revisions(owner_engine, ticket_id) == 1

    again = await client.post(f"/api/v1/pending-revisions/{draft_id}/approve", headers=headers, json={})
    assert again.status_code == 409

    listed = await client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
    assert listed.json()["priority"] == "critical"
    assert listed.json()["open_pending_revision"] is None


async def test_colleague_claim_is_409_and_other_organization_is_404(client, owner_engine):
    seeded = await _seed(owner_engine)
    owner = await auth_header(client, "op1@excellence.qai.local")
    colleague = await auth_header(client, "op2@excellence.qai.local")
    outsider = await auth_header(client, "op1@quantum.qai.local")
    claimed = await client.post(
        f"/api/v1/tickets/{seeded['ticket']}/pending-revisions",
        headers=owner,
        json={"action": "update", "changed_contents": {"title": "Working title"}},
    )
    draft_id = claimed.json()["id"]
    race = await client.post(
        f"/api/v1/tickets/{seeded['ticket']}/pending-revisions",
        headers=colleague,
        json={"action": "delete"},
    )
    assert race.status_code == 409
    assert race.json()["pending_revision_id"] == draft_id
    assert race.json()["owner"] == {"id": seeded["operator"], "name": "Ada"}

    missing = await client.get(f"/api/v1/pending-revisions/{draft_id}", headers=outsider)
    assert missing.status_code == 404
    hidden = await client.put(
        f"/api/v1/pending-revisions/{draft_id}",
        headers=colleague,
        json={"changed_contents": {"title": "Taken"}},
    )
    assert hidden.status_code == 404


async def test_tainted_draft_is_approved_by_the_lead_and_noted_in_chat(client, owner_engine):
    seeded = await _seed(owner_engine)
    operator = await auth_header(client, "op1@excellence.qai.local")
    lead = await auth_header(client, "lead@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", headers=operator, json={"title": "Drafts"})
    session_id = uuid.UUID(created.json()["id"])
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    context = OrganizationContext(seeded["org"], seeded["operator"], "operator")
    async with factory() as session:
        await bind_organization(session, seeded["org"])
        drafts = build_pending_revision_service(session, context)
        proposed = await drafts.propose(
            ticket_id=seeded["ticket"],
            action="update",
            fields={"priority": "high"},
            tainted=True,
            session_id=session_id,
        )
    await engine.dispose()
    assert proposed.draft is not None
    draft_id = str(proposed.draft.id)
    before = (await client.get(f"/api/v1/tickets/{seeded['ticket']}", headers=operator)).json()
    assert before["priority"] == "low"
    assert await _revisions(owner_engine, seeded["ticket"]) == 0

    denied = await client.post(f"/api/v1/pending-revisions/{draft_id}/approve", headers=operator, json={})
    assert denied.status_code == 403
    lead_save = await client.put(
        f"/api/v1/pending-revisions/{draft_id}",
        headers=lead,
        json={"changed_contents": {"priority": "critical"}},
    )
    assert lead_save.status_code == 403
    queue = await client.get("/api/v1/pending-revisions", headers=operator, params={"scope": "lead_queue"})
    assert queue.status_code == 403
    visible = await client.get("/api/v1/pending-revisions", headers=lead, params={"scope": "lead_queue"})
    assert visible.status_code == 200
    assert [item["id"] for item in visible.json()] == [draft_id]

    approved = await client.post(
        f"/api/v1/pending-revisions/{draft_id}/approve",
        headers=lead,
        json={"changed_contents": {"priority": "critical"}},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["ticket"]["priority"] == "critical"
    assert await _revisions(owner_engine, seeded["ticket"]) == 1
    history = await client.get(f"/api/v1/chat/sessions/{session_id}", headers=operator)
    notes = [message for message in history.json()["messages"] if message["role"] == "system"]
    assert notes
    assert notes[0]["parts"][0]["text"] == f"Pending revision {draft_id} was executed by Cara"
    assert "Billing" not in notes[0]["parts"][0]["text"]


async def test_stale_approve_leaves_the_draft_open(client, owner_engine):
    seeded = await _seed(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    claimed = await client.post(
        f"/api/v1/tickets/{seeded['ticket']}/pending-revisions",
        headers=headers,
        json={"action": "update", "changed_contents": {"status": "closed"}},
    )
    draft_id = claimed.json()["id"]
    async with owner_engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO revisions (id, ticket_id, organization_id, user_id, initial_contents, changed_contents) "
                "VALUES (:id, :ticket_id, :organization_id, :user_id, "
                "CAST(:snapshot AS jsonb), CAST(:snapshot AS jsonb))"
            ),
            {
                "id": str(uuid.uuid4()),
                "ticket_id": seeded["ticket"],
                "organization_id": seeded["org"],
                "user_id": seeded["operator"],
                "snapshot": (
                    '{"title":"Billing export","contents":"The client wrote this.","status":"open","priority":"low"}'
                ),
            },
        )
    stale = await client.post(f"/api/v1/pending-revisions/{draft_id}/approve", headers=headers, json={})
    assert stale.status_code == 409
    still = await client.get(f"/api/v1/pending-revisions/{draft_id}", headers=headers)
    assert still.json()["status"] == "open"


async def test_expired_agent_draft_is_410_and_delete_hides_the_ticket(client, owner_engine):
    seeded = await _seed(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    context = OrganizationContext(seeded["org"], seeded["operator"], "operator")
    async with factory() as session:
        await bind_organization(session, seeded["org"])
        created = await client.post("/api/v1/chat/sessions", headers=headers, json={})
        session_id = uuid.UUID(created.json()["id"])
        proposed = await build_pending_revision_service(session, context).propose(
            ticket_id=seeded["ticket"],
            action="delete",
            fields={},
            tainted=False,
            session_id=session_id,
        )
        draft_id = proposed.draft.id
    await engine.dispose()
    async with owner_engine.begin() as connection:
        await connection.execute(
            text("UPDATE pending_revisions SET expires_at = :expires_at WHERE id = :id"),
            {"expires_at": datetime.now(UTC) - timedelta(minutes=1), "id": draft_id},
        )
    gone = await client.post(f"/api/v1/pending-revisions/{draft_id}/approve", headers=headers, json={})
    assert gone.status_code == 410
    assert await _revisions(owner_engine, seeded["ticket"]) == 0

    fresh = await client.post(
        f"/api/v1/tickets/{seeded['ticket']}/pending-revisions",
        headers=headers,
        json={"action": "delete"},
    )
    assert fresh.status_code == 201, fresh.text
    removed = await client.post(f"/api/v1/pending-revisions/{fresh.json()['id']}/approve", headers=headers, json={})
    assert removed.status_code == 200, removed.text
    assert (await client.get(f"/api/v1/tickets/{seeded['ticket']}", headers=headers)).status_code == 404
    listed = await client.get("/api/v1/tickets", headers=headers, params={"q": "Billing export"})
    assert listed.json()["items"] == []


async def test_foreign_ticket_matches_unknown_and_writes_no_revision(client, owner_engine):
    seeded = await _seed(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", headers=headers, json={})
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    context = OrganizationContext(seeded["org"], seeded["operator"], "operator")

    async def run(ticket_id: int):
        async with factory() as session:
            await bind_organization(session, seeded["org"])
            tool = MutateTicketTool(build_pending_revision_service(session, context))
            ctx = ToolContext(organization=context, session_id=uuid.UUID(created.json()["id"]), db=session)
            args = tool.args_model.model_validate({"id": ticket_id, "action": "update", "fields": {"priority": "high"}})
            return await tool.run(args, ctx)

    unknown = await run(999999)
    foreign = await run(seeded["foreign"])
    await engine.dispose()
    assert unknown.ok is False and foreign.ok is False
    assert unknown.error == foreign.error
    assert await _revisions(owner_engine, seeded["foreign"]) == 0
    assert await _revisions(owner_engine, seeded["ticket"]) == 0


async def test_concurrent_claims_produce_one_winner(owner_engine):
    seeded = await _seed(owner_engine)
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    context = OrganizationContext(seeded["org"], seeded["operator"], "operator")

    async def attempt() -> str:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            await bind_organization(session, seeded["org"])
            try:
                await build_pending_revision_service(session, context).claim(seeded["ticket"], "update", None)
            except Exception as exc:
                from src.core.exceptions import ConflictError

                if isinstance(exc, ConflictError):
                    return "conflict"
                raise
        return "created"

    try:
        results = await asyncio.gather(*(attempt() for _ in range(2)))
    finally:
        await engine.dispose()
    assert sorted(results) == ["conflict", "created"]


async def test_audit_is_scoped_and_append_only(client, owner_engine):
    seeded = await _seed(owner_engine)
    operator = await auth_header(client, "op1@excellence.qai.local")
    colleague = await auth_header(client, "op2@excellence.qai.local")
    lead = await auth_header(client, "lead@excellence.qai.local")
    claimed = await client.post(
        f"/api/v1/tickets/{seeded['ticket']}/pending-revisions",
        headers=operator,
        json={"action": "update", "changed_contents": {"status": "blocked"}},
    )
    assert claimed.status_code == 201
    own = await client.get("/api/v1/audit", headers=operator)
    assert own.status_code == 200
    own_events = {item["event"] for item in own.json()["items"]}
    assert "login" in own_events
    assert "pending_revision_created" in own_events
    assert all(item["actor"]["id"] == seeded["operator"] for item in own.json()["items"] if item["actor"])
    other = await client.get("/api/v1/audit", headers=colleague)
    assert "pending_revision_created" not in {item["event"] for item in other.json()["items"]}
    org = await client.get("/api/v1/audit", headers=lead, params={"ticket_id": seeded["ticket"]})
    assert "pending_revision_created" in {item["event"] for item in org.json()["items"]}
    hidden = await client.get("/api/v1/audit", headers=lead, params={"ticket_id": seeded["foreign"]})
    assert hidden.status_code == 404

    app_engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        async with app_engine.connect() as connection:
            await connection.execute(
                text("SELECT set_config('app.organization_id', :value, true)"),
                {"value": str(seeded["org"])},
            )
            with pytest.raises(Exception):
                await connection.execute(text("UPDATE audit_events SET event = 'tampered'"))
    finally:
        await app_engine.dispose()


async def test_agent_drafts_a_change_and_approve_is_what_writes_the_ticket(app, client, owner_engine):
    seeded = await _seed(owner_engine)
    call = ToolCall(
        "call-close",
        "mutate_ticket",
        {"id": seeded["ticket"], "action": "update", "fields": {"priority": "high"}},
    )
    fake = FakeLLMClient(
        [
            [TurnComplete(LLMMessage(role="assistant", tool_calls=(call,), model="fake"))],
            [TextDelta("Drafted."), TurnComplete(LLMMessage(role="assistant", text="Drafted.", model="fake"))],
        ]
    )
    app.dependency_overrides[get_llm_client] = lambda: fake
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={"title": "Gate"}, headers=headers)
    try:
        async with client.stream(
            "POST",
            f"/api/v1/chat/sessions/{created.json()['id']}/messages",
            json={"text": "close the billing ticket"},
            headers=headers,
        ) as response:
            assert response.status_code == 200
            events = await read_events(response)
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    assert "approval_required" in [event["type"] for event in events]
    approval = next(event for event in events if event["type"] == "approval_required")
    draft_id = approval["pending_revision"]["id"]
    before = await client.get(f"/api/v1/tickets/{seeded['ticket']}", headers=headers)
    assert before.json()["priority"] == "low"
    assert await _revisions(owner_engine, seeded["ticket"]) == 0
    approved = await client.post(
        f"/api/v1/pending-revisions/{draft_id}/approve",
        headers=headers,
        json={"changed_contents": {"priority": "critical"}},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["ticket"]["priority"] == "critical"
    assert await _revisions(owner_engine, seeded["ticket"]) == 1
    history = await client.get(f"/api/v1/chat/sessions/{created.json()['id']}", headers=headers)
    tool_parts = [part for message in history.json()["messages"] for part in message["parts"] if part["kind"] == "tool"]
    assert tool_parts[0]["pending_revision_status"] == "executed"
    audit = await client.get("/api/v1/audit", headers=headers, params={"ticket_id": seeded["ticket"]})
    events_logged = {item["event"] for item in audit.json()["items"]}
    assert {"pending_revision_created", "pending_revision_approved", "ticket_mutated", "tool_called"} <= events_logged
