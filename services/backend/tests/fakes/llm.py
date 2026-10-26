import asyncio
from collections.abc import AsyncIterator

from src.integrations.llm.types import LLMError, LLMEvent, LLMMessage


class FakeLLMClient:
    """Pops one scripted turn per ``stream`` call. An exception in the script is raised there."""

    def __init__(self, script: list[list[LLMEvent | LLMError]], model: str = "fake-model", delay: float = 0.0):
        self.script = script
        self._model = model
        self.delay = delay
        self.calls: list[tuple[list[LLMMessage], str | None]] = []
        self.last_tools = None

    @property
    def model(self) -> str:
        return self._model

    async def stream(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
        tools: list | None = None,
    ) -> AsyncIterator[LLMEvent]:
        self.calls.append((messages, system))
        self.last_tools = tools
        events = self.script.pop(0)
        for event in events:
            if self.delay:
                await asyncio.sleep(self.delay)
            if isinstance(event, Exception):
                raise event
            yield event
