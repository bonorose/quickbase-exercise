import pytest
from tests.factories import commit_operator
from tests.fakes.llm import FakeLLMClient
from tests.helpers.auth import auth_header
from tests.helpers.sse import read_events

from src.integrations.llm import Completed, LLMError, Notice, TextDelta, get_llm_client

pytestmark = pytest.mark.api


async def test_scripted_stream_order(app, client, owner_engine):
    fake = FakeLLMClient(
        [
            [
                Notice("Waiting for fake-model…"),
                TextDelta("one"),
                TextDelta("two"),
                TextDelta("three"),
                Completed("onetwothree", "fake-model"),
            ]
        ]
    )
    app.dependency_overrides[get_llm_client] = lambda: fake
    await commit_operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    try:
        async with client.stream("POST", "/api/v1/llm/stream", json={"prompt": "hello"}, headers=headers) as response:
            assert response.status_code == 200
            events = await read_events(response)
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    assert [event["type"] for event in events] == ["status", "delta", "delta", "delta", "done"]


async def test_mid_stream_error_is_an_event(app, client, owner_engine):
    fake = FakeLLMClient([[TextDelta("partial"), LLMError("model failed")]])
    app.dependency_overrides[get_llm_client] = lambda: fake
    await commit_operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    try:
        async with client.stream("POST", "/api/v1/llm/stream", json={"prompt": "hello"}, headers=headers) as response:
            assert response.status_code == 200
            events = await read_events(response)
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    assert events[-1]["type"] == "error"


async def test_missing_client_is_503_before_streaming(client, owner_engine):
    await commit_operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    response = await client.post("/api/v1/llm/stream", json={"prompt": "hello"}, headers=headers)
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")
