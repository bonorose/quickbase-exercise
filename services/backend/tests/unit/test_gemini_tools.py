import pytest
from google.genai import types

from src.integrations.llm.gemini import FOREIGN_SIGNATURE, GeminiClient
from src.integrations.llm.types import LLMMessage, TextDelta, ToolCall, ToolSpec, TurnComplete

pytestmark = pytest.mark.unit


def _client() -> GeminiClient:
    client = GeminiClient(
        api_key="test",
        model="gemini-3.8-flash",
        fallback_models=["gemini-3.5-flash"],
        first_chunk_timeout_seconds=5,
        request_timeout_seconds=30,
        max_retries=0,
        temperature=0,
    )
    return client


def test_replay_uses_raw_for_the_same_model_and_foreign_signature_otherwise():
    raw = types.Content(
        role="model",
        parts=[
            types.Part(
                function_call=types.FunctionCall(id="c1", name="search_tickets", args={"query": "billing"}),
                thought_signature=b"original-signature",
            )
        ],
    )
    history = [
        LLMMessage(role="user", text="what's blocked?"),
        LLMMessage(
            role="assistant",
            text="",
            tool_calls=(ToolCall("c1", "search_tickets", {"query": "billing"}),),
            raw=raw,
            model="gemini-3.8-flash",
        ),
    ]
    same = GeminiClient._to_contents(history, "gemini-3.8-flash")
    assert same[1] is raw
    other = GeminiClient._to_contents(history, "gemini-3.5-flash")
    assert other[1].parts[0].thought_signature == FOREIGN_SIGNATURE


def test_raw_round_trip_keeps_signature_bytes():
    raw = types.Content(
        role="model",
        parts=[types.Part(text="hello", thought_signature=b"\x00\xffsignature")],
    )
    restored = GeminiClient.deserialize_raw(GeminiClient.serialize_raw(raw))
    assert restored is not None
    assert restored.parts[0].thought_signature == b"\x00\xffsignature"


async def test_function_call_becomes_turn_complete_and_thoughts_stay_silent():
    function_part = types.Part(
        function_call=types.FunctionCall(id="c1", name="search_tickets", args={"query": "billing"})
    )
    thought = types.Part(text="hidden", thought=True, thought_signature=b"sig")
    spoken = types.Part(text="visible")
    chunks = [
        types.GenerateContentResponse(
            candidates=[types.Candidate(content=types.Content(role="model", parts=[thought, spoken, function_part]))]
        )
    ]
    captured: list = []

    class Models:
        async def generate_content_stream(self, *, model, contents, config):
            captured.append(config)

            async def generate():
                for chunk in chunks:
                    yield chunk

            return generate()

    class Aio:
        models = Models()

    class SDK:
        aio = Aio()

    client = _client()
    client._client = SDK()
    spec = ToolSpec(name="search_tickets", description="search", parameters={"type": "object"})
    events = [event async for event in client.stream([LLMMessage(role="user", text="hi")], tools=[spec])]
    assert not any(isinstance(event, TextDelta) and event.text == "hidden" for event in events)
    assert any(isinstance(event, TextDelta) and event.text == "visible" for event in events)
    done = events[-1]
    assert isinstance(done, TurnComplete)
    assert done.turn.tool_calls[0].name == "search_tickets"
    assert done.turn.tool_calls[0].args == {"query": "billing"}
    assert captured[0].automatic_function_calling.disable is True


@pytest.mark.live
async def test_live_gemini_tool_call():
    import os

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        pytest.skip("GEMINI_API_KEY is not set; live Gemini stays out of CI")
    client = GeminiClient(
        api_key=key,
        model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
        fallback_models=[],
        first_chunk_timeout_seconds=20,
        request_timeout_seconds=60,
        max_retries=0,
        temperature=0,
    )
    spec = ToolSpec(name="search_tickets", description="search", parameters={"type": "object"})
    events = [
        event
        async for event in client.stream(
            [LLMMessage(role="user", text="Reply with the single word pong.")],
            tools=[spec],
        )
    ]
    assert events
    assert isinstance(events[-1], TurnComplete)
