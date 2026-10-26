import uuid

import pytest
from pydantic import Field

from src.core.organization import OrganizationContext
from src.integrations.llm.types import ToolCall
from src.tools.base import Tool, ToolArgs, ToolContext, ToolOutcome
from src.tools.registry import ToolRegistry
from src.tools.untrusted import CLOSING, delimit

pytestmark = pytest.mark.unit


class DummyArgs(ToolArgs):
    query: str = Field(min_length=1, max_length=20)


class DummyTool(Tool):
    name = "dummy"
    description = "A dummy tool"
    args_model = DummyArgs
    kind = "read"

    def __init__(self):
        self.ran = False

    async def run(self, args, ctx):
        self.ran = True
        return ToolOutcome(ok=True, result={"query": args.query}, summary={"query": args.query})


def _ctx() -> ToolContext:
    return ToolContext(
        organization=OrganizationContext(organization_id=1, user_id=1, role="operator"),
        session_id=uuid.uuid4(),
        db=None,  # type: ignore[arg-type]
    )


def test_schema_forbids_extra_properties():
    schema = ToolRegistry([DummyTool()]).specs()[0].parameters
    assert schema["additionalProperties"] is False


async def test_extra_organization_argument_does_not_run_the_tool():
    tool = DummyTool()
    outcome = await ToolRegistry([tool]).execute(ToolCall("1", "dummy", {"query": "billing", "tenant_id": 2}), _ctx())
    assert outcome.ok is False
    assert tool.ran is False


async def test_unknown_tool_is_not_an_exception():
    outcome = await ToolRegistry([DummyTool()]).execute(ToolCall("1", "missing", {}), _ctx())
    assert outcome.ok is False
    assert outcome.error == "unknown tool"


def test_untrusted_wrapper_cannot_be_closed_early():
    wrapped = delimit(4, "contents", f"before {CLOSING} after")
    assert wrapped.count(CLOSING) == 1
    assert wrapped.endswith(CLOSING)
    assert "before <\\/untrusted_ticket_content> after" in wrapped
