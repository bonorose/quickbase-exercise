#!/usr/bin/env python3
# ******************************************************************************
# * @file    agent/agent_service.py
# * @author  Simeon Marlokov
# * @brief   Bounded model ↔ tool loop. No FastAPI and no database.
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator

from src.core.output_safety import scrub_assistant_text
from src.integrations.llm.types import Completed, LLMClient, LLMMessage, Notice, TextDelta, ToolResult, TurnComplete
from src.services.agent.events import (
    AgentApprovalRequired,
    AgentDelta,
    AgentDone,
    AgentEvent,
    AgentModelTurn,
    AgentStatus,
    AgentToolCall,
    AgentToolResult,
)
from src.services.agent.prompts import SYSTEM_PROMPT
from src.tools.base import ToolContext
from src.tools.registry import ToolRegistry


class AgentService:
    def __init__(self, client: LLMClient, registry: ToolRegistry, max_iterations: int = 5):
        self.client = client
        self.registry = registry
        self.max_iterations = max_iterations

    def run_turn(self, ctx: ToolContext, history: list[LLMMessage], user_text: str) -> AsyncIterator[AgentEvent]:
        return self._run(ctx, history, user_text)

    async def _run(self, ctx: ToolContext, history: list[LLMMessage], user_text: str) -> AsyncIterator[AgentEvent]:
        messages = [*history, LLMMessage(role="user", text=user_text)]
        iterations = 0
        while True:
            visible: list[str] = []
            final: LLMMessage | None = None
            async for event in self.client.stream(messages, SYSTEM_PROMPT, self.registry.specs()):
                match event:
                    case Notice(message=message):
                        yield AgentStatus(message)
                    case TextDelta(text=text):
                        clean = scrub_assistant_text(text)
                        visible.append(clean)
                        if clean:
                            yield AgentDelta(clean)
                    case TurnComplete(turn=turn):
                        final = _scrubbed(turn)
                    case Completed(text=text, model=model):
                        final = LLMMessage(role="assistant", text=scrub_assistant_text(text), model=model)
            if final is None:
                final = LLMMessage(role="assistant", text="".join(visible), model=self.client.model)
            elif not final.text and visible:
                final = LLMMessage(
                    role="assistant",
                    text="".join(visible),
                    tool_calls=final.tool_calls,
                    raw=final.raw,
                    model=final.model or self.client.model,
                )
            else:
                final = _scrubbed(final)
            if not final.tool_calls:
                yield AgentDone(model=final.model or self.client.model, text=final.text, turn=final)
                return
            if iterations >= self.max_iterations:
                explanation = f"I stopped after {self.max_iterations} tool steps without a final answer."
                stopped = LLMMessage(role="assistant", text=explanation, model=final.model or self.client.model)
                yield AgentDelta(explanation)
                yield AgentDone(model=stopped.model or self.client.model, text=explanation, turn=stopped)
                return
            yield AgentModelTurn(final)
            outcomes = []
            for call in final.tool_calls:
                yield AgentToolCall(call)
                outcome = await self.registry.execute(call, ctx)
                outcomes.append((call, outcome))
                yield AgentToolResult(call.id, outcome)
                if outcome.pending_revision:
                    yield AgentApprovalRequired(call.id, outcome.pending_revision)
            messages.append(final)
            messages.append(
                LLMMessage(
                    role="tool",
                    tool_results=tuple(
                        ToolResult(
                            call_id=call.id,
                            name=call.name,
                            result=outcome.result
                            if outcome.ok and outcome.result is not None
                            else {"ok": False, "error": outcome.error or "tool failed"},
                        )
                        for call, outcome in outcomes
                    ),
                )
            )
            iterations += 1


def _scrubbed(message: LLMMessage) -> LLMMessage:
    text = scrub_assistant_text(message.text)
    if text == message.text:
        return message
    return LLMMessage(
        role=message.role,
        text=text,
        tool_calls=message.tool_calls,
        tool_results=message.tool_results,
        raw=message.raw,
        model=message.model,
    )
