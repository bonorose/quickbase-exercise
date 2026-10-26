import json
import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker
from tests.factories import make_organization, make_ticket, make_user
from tests.fakes.llm import FakeLLMClient
from tests.helpers.auth import auth_header
from tests.helpers.sse import read_events

from src.core.organization import OrganizationContext
from src.db.session import bind_organization, get_session_factory
from src.integrations.llm import LLMQuotaExhaustedError, TextDelta, ToolCall, TurnComplete, get_llm_client
from src.integrations.llm.types import LLMMessage
from src.models.user import User
from src.repositories.chat_message_repository import ChatMessageRepository
from src.repositories.chat_session_repository import ChatSessionRepository
from src.services.chat_service import ChatService
from src.tools.base import Tool, ToolArgs, ToolOutcome

pytestmark = pytest.mark.api


def _billing_script():
    call = ToolCall("call-billing", "search_tickets", {"query": "billing", "status": "blocked"})
    return FakeLLMClient(
        [
            [TurnComplete(LLMMessage(role="assistant", tool_calls=(call,), model="fake"))],
            [
                TextDelta("The billing export is blocked."),
                TurnComplete(LLMMessage(role="assistant", text="The billing export is blocked.", model="fake")),
            ],
        ]
    )


async def _two_teams(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        excellence = await make_organization(session, "Excellence")
        quantum = await make_organization(session, "Quantum Workflow")
        operator = await make_user(session, excellence, email="op1@excellence.qai.local", name="Operator One")
        teammate = await make_user(session, excellence, email="op2@excellence.qai.local", name="Operator Two")
        await make_user(session, quantum, email="op1@quantum.qai.local", name="Quantum Operator")
        await make_ticket(
            session,
            excellence,
            title="Billing export fails",
            status=2,
            description="Neutral billing summary.",
            contents="Client billing details.",
            updated_by=operator.id,
        )
        await make_ticket(
            session,
            quantum,
            title="Quantum billing secret",
            status=2,
            description="Quantum only.",
            contents="Do not leak.",
        )
        await session.commit()
        return operator.id, teammate.id


async def test_sessions_are_private_to_the_owner(client, owner_engine):
    await _two_teams(owner_engine)
    owner = await auth_header(client, "op1@excellence.qai.local")
    teammate = await auth_header(client, "op2@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={}, headers=owner)
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "New conversation"
    assert set(body) == {"id", "title", "date_created", "last_activity_at"}
    unknown_id = uuid.uuid4()
    missing = await client.get(f"/api/v1/chat/sessions/{unknown_id}", headers=owner)
    foreign = await client.get(f"/api/v1/chat/sessions/{body['id']}", headers=teammate)
    assert missing.status_code == 404
    assert foreign.status_code == 404
    assert missing.json()["detail"] == f"Chat session {unknown_id} not found"
    assert foreign.json()["detail"] == f"Chat session {body['id']} not found"


async def test_detail_hides_raw_and_folds_tool_results(client, owner_engine):
    organization_id, user_id = await _operator(owner_engine)
    owner = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={"title": "Standup"}, headers=owner)
    session_id = uuid.UUID(created.json()["id"])
    organization = OrganizationContext(organization_id, user_id, "operator")
    async with get_session_factory()() as db:
        await bind_organization(db, organization_id)
        chat = await ChatSessionRepository(db, organization).get_owned(session_id)
        messages = ChatMessageRepository(db, organization)
        await messages.append(
            chat,
            role="assistant",
            model="fake",
            content={
                "parts": [
                    {"kind": "text", "text": "Looking."},
                    {"kind": "tool", "call_id": "c1", "name": "search_tickets", "args": {"query": "billing"}},
                ],
                "raw": {"secret": True},
            },
        )
        await messages.append(
            chat,
            role="tool",
            content={
                "parts": [
                    {
                        "kind": "tool",
                        "call_id": "c1",
                        "name": "search_tickets",
                        "args": {"query": "billing"},
                        "ok": True,
                        "result": {"count": 1, "tickets": [{"id": 1, "title": "Billing"}]},
                        "model_result": {
                            "tickets": [{"description": "<untrusted_ticket_content>secret</untrusted_ticket_content>"}]
                        },
                    }
                ]
            },
        )
    detail = await client.get(f"/api/v1/chat/sessions/{session_id}", headers=owner)
    assert detail.status_code == 200
    payload = detail.text
    assert "raw" not in payload
    assert "model_result" not in payload
    assert "untrusted_ticket_content" not in payload
    tool_parts = [part for part in detail.json()["messages"][0]["parts"] if part["kind"] == "tool"]
    assert tool_parts[0]["result"]["count"] == 1


async def _operator(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        organization = await make_organization(session, "Excellence")
        user = await make_user(session, organization, email="op1@excellence.qai.local")
        await session.commit()
        return organization.id, user.id


async def test_stream_searches_only_the_caller_organization(app, client, owner_engine):
    await _two_teams(owner_engine)
    fake = _billing_script()
    app.dependency_overrides[get_llm_client] = lambda: fake
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={}, headers=headers)
    try:
        async with client.stream(
            "POST",
            f"/api/v1/chat/sessions/{created.json()['id']}/messages",
            json={"text": "what's blocked on billing?"},
            headers=headers,
        ) as response:
            assert response.status_code == 200
            events = await read_events(response)
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    assert [event["type"] for event in events] == ["session", "tool_call", "tool_result", "delta", "done"]
    result = events[2]["result"]
    assert result["count"] == 1
    assert result["tickets"][0]["title"] == "Billing export fails"
    assert "description" not in json.dumps(result)
    assert "contents" not in json.dumps(result)
    replay = fake.calls[1][0][-1].tool_results[0].result
    assert "Quantum" not in json.dumps(replay)
    assert "<untrusted_ticket_content" in json.dumps(replay)


async def test_missing_model_is_503_before_streaming(client, owner_engine):
    await _operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={}, headers=headers)
    response = await client.post(
        f"/api/v1/chat/sessions/{created.json()['id']}/messages",
        json={"text": "hello"},
        headers=headers,
    )
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")


async def test_quota_and_internal_errors_are_typed(app, client, owner_engine):
    organization_id, user_id = await _operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={}, headers=headers)
    session_id = created.json()["id"]
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient([[LLMQuotaExhaustedError("used up", 60)]])
    try:
        async with client.stream(
            "POST",
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"text": "quota please"},
            headers=headers,
        ) as response:
            assert response.status_code == 200
            events = await read_events(response)
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    assert events[-1]["code"] == "quota_exhausted"
    assert "Traceback" not in events[-1]["message"]

    class Boom(Tool):
        name = "search_tickets"
        description = "boom"
        args_model = ToolArgs
        kind = "read"

        async def run(self, args, ctx):
            raise RuntimeError("secret stack")

    fake = FakeLLMClient(
        [[TurnComplete(LLMMessage(role="assistant", tool_calls=(ToolCall("1", "search_tickets", {}),), model="fake"))]]
    )
    organization = OrganizationContext(organization_id, user_id, "operator")
    async with get_session_factory()() as db:
        await bind_organization(db, organization_id)
        service = ChatService(
            ChatSessionRepository(db, organization),
            ChatMessageRepository(db, organization),
            fake,
            max_iterations=5,
            history_limit=40,
            tools=[Boom()],
        )
        streamed = [event async for event in service.stream_message(uuid.UUID(session_id), "explode")]
    assert streamed[-1].code == "internal"
    assert "secret" not in streamed[-1].message


async def test_disconnect_keeps_finished_turns_only(app, client, owner_engine):
    organization_id, user_id = await _operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={}, headers=headers)
    session_id = uuid.UUID(created.json()["id"])
    call = ToolCall("c1", "search_tickets", {"query": "billing"})
    fake = FakeLLMClient(
        [
            [TurnComplete(LLMMessage(role="assistant", tool_calls=(call,), model="fake"))],
            [TextDelta("partial answer that must not be stored")],
        ]
    )

    class Quiet(Tool):
        name = "search_tickets"
        description = "quiet"
        args_model = ToolArgs
        kind = "read"

        async def run(self, args, ctx):
            return ToolOutcome(ok=True, result={"tickets": [], "total": 0}, summary={"count": 0, "tickets": []})

    organization = OrganizationContext(organization_id, user_id, "operator")
    async with get_session_factory()() as db:
        await bind_organization(db, organization_id)
        user = await db.get(User, user_id)
        assert user is not None
        service = ChatService(
            ChatSessionRepository(db, organization),
            ChatMessageRepository(db, organization),
            fake,
            max_iterations=5,
            history_limit=40,
            tools=[Quiet()],
        )
        generator = service.stream_message(session_id, "what's blocked?")
        seen = []
        async for event in generator:
            seen.append(event.type)
            if event.type == "tool_result":
                await generator.aclose()
                break
    async with get_session_factory()() as db:
        await bind_organization(db, organization_id)
        rows = await ChatMessageRepository(db, organization).list_for_session(session_id)
    roles = [row.role for row in rows]
    assert roles == ["user", "assistant", "tool"]
    assert all("partial answer" not in json.dumps(row.content) for row in rows)
    assert seen == ["session", "tool_call", "tool_result"]


async def test_reloaded_history_includes_the_tool_turn(app, client, owner_engine):
    await _operator(owner_engine)
    call = ToolCall("c1", "search_tickets", {"query": "billing"})
    fake = FakeLLMClient(
        [
            [TurnComplete(LLMMessage(role="assistant", tool_calls=(call,), model="fake"))],
            [TextDelta("first"), TurnComplete(LLMMessage(role="assistant", text="first", model="fake"))],
            [TextDelta("second"), TurnComplete(LLMMessage(role="assistant", text="second", model="fake"))],
        ]
    )
    app.dependency_overrides[get_llm_client] = lambda: fake
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={}, headers=headers)
    session_id = created.json()["id"]
    try:
        async with client.stream(
            "POST", f"/api/v1/chat/sessions/{session_id}/messages", json={"text": "first question"}, headers=headers
        ) as response:
            assert response.status_code == 200
            await read_events(response)
        async with client.stream(
            "POST", f"/api/v1/chat/sessions/{session_id}/messages", json={"text": "second question"}, headers=headers
        ) as response:
            assert response.status_code == 200
            await read_events(response)
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    history = fake.calls[-1][0]
    assert any(message.role == "tool" for message in history)
    assert history[-1].text == "second question"
