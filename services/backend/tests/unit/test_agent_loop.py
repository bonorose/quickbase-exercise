import uuid

import pytest
from tests.fakes.llm import FakeLLMClient

from src.core.organization import OrganizationContext
from src.integrations.llm.types import LLMMessage, TextDelta, ToolCall, TurnComplete
from src.services.agent.agent_service import AgentService
from src.services.agent.events import AgentDone, AgentToolResult
from src.tools.base import Tool, ToolArgs, ToolContext, ToolOutcome
from src.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


class Args(ToolArgs):
    query: str | None = None


class Dummy(Tool):
    name = "search_tickets"
    description = "search"
    args_model = Args
    kind = "read"

    async def run(self, args, ctx):
        return ToolOutcome(ok=True, result={"tickets": [], "total": 0}, summary={"count": 0, "tickets": []})


class Exploding(Tool):
    name = "explode"
    description = "explode"
    args_model = Args
    kind = "read"

    async def run(self, args, ctx):
        raise RuntimeError("secret stack")


def _ctx() -> ToolContext:
    return ToolContext(
        organization=OrganizationContext(1, 1, "operator"),
        session_id=uuid.uuid4(),
        db=None,  # type: ignore[arg-type]
    )


def _call(name: str = "search_tickets", args: dict | None = None, call_id: str = "1") -> ToolCall:
    return ToolCall(call_id, name, args or {"query": "billing"})


async def _events(agent: AgentService):
    return [event async for event in agent.run_turn(_ctx(), [], "what's blocked?")]


async def test_search_then_answer_order():
    fake = FakeLLMClient(
        [
            [TurnComplete(LLMMessage(role="assistant", tool_calls=(_call(),), model="fake"))],
            [TextDelta("Found it."), TurnComplete(LLMMessage(role="assistant", text="Found it.", model="fake"))],
        ]
    )
    events = await _events(AgentService(fake, ToolRegistry([Dummy()]), max_iterations=5))
    kinds = [type(event) for event in events]
    assert [kind.__name__ for kind in kinds] == [
        "AgentModelTurn",
        "AgentToolCall",
        "AgentToolResult",
        "AgentDelta",
        "AgentDone",
    ]
    assert events[1].call.name == "search_tickets"
    assert events[2].outcome.ok is True
    assert fake.calls[1][0][-1].role == "tool"


async def test_iteration_cap_stops_and_limits_model_calls():
    fake = FakeLLMClient(
        [
            [TurnComplete(LLMMessage(role="assistant", tool_calls=(_call(call_id=str(i)),), model="fake"))]
            for i in range(6)
        ]
    )
    events = await _events(AgentService(fake, ToolRegistry([Dummy()]), max_iterations=2))
    assert len(fake.calls) == 3
    assert isinstance(events[-1], AgentDone)
    assert "stopped after 2" in events[-2].text


async def test_invalid_tool_arguments_are_fed_back():
    fake = FakeLLMClient(
        [
            [
                TurnComplete(
                    LLMMessage(role="assistant", tool_calls=(_call("search_tickets", {"limit": 50}),), model="fake")
                )
            ],
            [TextDelta("ok"), TurnComplete(LLMMessage(role="assistant", text="ok", model="fake"))],
        ]
    )
    events = await _events(AgentService(fake, ToolRegistry([Dummy()]), max_iterations=5))
    result = next(event for event in events if isinstance(event, AgentToolResult))
    assert result.outcome.ok is False
    assert fake.calls[1][0][-1].tool_results[0].result["ok"] is False


async def test_tool_exception_propagates():
    fake = FakeLLMClient([[TurnComplete(LLMMessage(role="assistant", tool_calls=(_call("explode"),), model="fake"))]])
    with pytest.raises(RuntimeError, match="secret stack"):
        await _events(AgentService(fake, ToolRegistry([Exploding()]), max_iterations=5))
