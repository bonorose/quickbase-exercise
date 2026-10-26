import pytest

from src.core.config import get_settings
from src.integrations.llm import assert_llm_provider_allowed, get_llm_client
from src.integrations.llm.fake import ScriptedLLMClient, load_scripts
from src.integrations.llm.types import LLMMessage, ToolSpec, TurnComplete

pytestmark = pytest.mark.unit


def test_production_refuses_the_fake_provider(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="production"):
        assert_llm_provider_allowed()


async def test_unknown_prompt_echoes():
    client = ScriptedLLMClient({})
    spec = ToolSpec(name="search_tickets", description="search", parameters={})
    events = [event async for event in client.stream([LLMMessage(role="user", text="Hello there")], tools=[spec])]
    assert isinstance(events[-1], TurnComplete)
    assert events[-1].turn.text == "Hello there"


def test_yaml_script_loads():
    from pathlib import Path

    scripts = load_scripts(str(Path(__file__).parents[1] / "fixtures" / "llm_scripts"))
    assert "what's blocked on billing?" in scripts
    assert scripts["what's blocked on billing?"].tool_calls[0].name == "search_tickets"


def test_get_llm_client_returns_scripted_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setenv("LLM_FAKE_SCRIPT_PATH", "")
    get_settings.cache_clear()
    get_llm_client.cache_clear()
    client = get_llm_client()
    assert isinstance(client, ScriptedLLMClient)
    get_llm_client.cache_clear()
