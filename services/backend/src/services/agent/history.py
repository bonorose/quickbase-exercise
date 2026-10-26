#!/usr/bin/env python3
# ******************************************************************************
# * @file    agent/history.py
# * @author  Simeon Marlokov
# * @brief   Rebuild provider turns from stored messages and write completed turns.
# * @date    25.10.2026
# ******************************************************************************
import json
import uuid

from src.integrations.llm.gemini import GeminiClient
from src.integrations.llm.types import LLMMessage, ToolCall, ToolResult
from src.models.chat_message import ChatMessage
from src.models.chat_session import ChatSession
from src.repositories.chat_message_repository import ChatMessageRepository
from src.schemas.chat.storage import StoredMessage, StoredTextPart, StoredToolPart
from src.tools.base import ToolOutcome
from src.tools.untrusted import OPENING


def auto_title(text: str, limit: int = 60) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned or "New conversation"
    cut = cleaned[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut or cleaned[:limit]


def to_llm_messages(rows: list[ChatMessage], *, full_after: int) -> list[LLMMessage]:
    """Messages at index >= full_after keep provider raw and the full tool payload."""
    turns: list[LLMMessage] = []
    for index, row in enumerate(rows):
        stored = StoredMessage.model_validate(row.content)
        full = index >= full_after
        if row.role == "user":
            text = next((part.text for part in stored.parts if isinstance(part, StoredTextPart)), "")
            turns.append(LLMMessage(role="user", text=text))
        elif row.role == "assistant":
            text = "".join(part.text for part in stored.parts if isinstance(part, StoredTextPart))
            calls = tuple(
                ToolCall(id=part.call_id, name=part.name, args=part.args)
                for part in stored.parts
                if isinstance(part, StoredToolPart)
            )
            raw = GeminiClient.deserialize_raw(stored.raw) if full else None
            turns.append(LLMMessage(role="assistant", text=text, tool_calls=calls, raw=raw, model=row.model))
        elif row.role == "system":
            text = next((part.text for part in stored.parts if isinstance(part, StoredTextPart)), "")
            turns.append(LLMMessage(role="user", text=f"System note: {text}"))
        elif row.role == "tool":
            results = []
            for part in stored.parts:
                if not isinstance(part, StoredToolPart):
                    continue
                payload = part.model_result if full and part.model_result is not None else (part.result or {})
                if not full and part.model_result is not None and part.result is None and part.error:
                    payload = {"ok": False, "error": part.error}
                results.append(ToolResult(call_id=part.call_id, name=part.name, result=payload))
            turns.append(LLMMessage(role="tool", tool_results=tuple(results)))
    return turns


def rows_contain_untrusted(rows: list[ChatMessage]) -> bool:
    """True once any tool result in the session carried untrusted ticket text.

    Sticky for the whole session, not just the replay window: earlier assistant replies can
    paraphrase injected text long after the tool row that carried it has scrolled out.
    Rows stored before the ``untrusted`` flag existed are detected by the delimiter.
    """
    for row in rows:
        if row.role != "tool":
            continue
        for part in StoredMessage.model_validate(row.content).parts:
            if not isinstance(part, StoredToolPart):
                continue
            if part.untrusted:
                return True
            if part.model_result is not None and OPENING in json.dumps(part.model_result):
                return True
    return False


class HistoryStore:
    def __init__(self, messages: ChatMessageRepository, max_messages: int = 40):
        self.messages = messages
        self.max_messages = max_messages

    async def load(self, session_id: uuid.UUID) -> list[LLMMessage]:
        messages, _tainted = await self.load_for_turn(session_id)
        return messages

    async def load_for_turn(self, session_id: uuid.UUID) -> tuple[list[LLMMessage], bool]:
        """The replayed history and whether the session has already seen untrusted content."""
        rows = list(await self.messages.list_for_session(session_id))
        full_after = max(0, len(rows) - self.max_messages)
        window = rows if len(rows) <= self.max_messages else rows[full_after:]
        # Older rows are omitted. Tool rows inside the window stay complete.
        return to_llm_messages(window, full_after=0), rows_contain_untrusted(rows)

    async def trimmed_tool_payload(self, session_id: uuid.UUID) -> list[dict | None]:
        """Expose how tool payloads look once they fall outside the window. Used by tests."""
        rows = list(await self.messages.list_for_session(session_id))
        full_after = max(0, len(rows) - self.max_messages)
        return [
            next(
                (
                    part.model_result if index >= full_after and part.model_result is not None else part.result
                    for part in StoredMessage.model_validate(row.content).parts
                    if isinstance(part, StoredToolPart)
                ),
                None,
            )
            for index, row in enumerate(rows)
            if row.role == "tool"
        ]

    async def append_user(self, chat: ChatSession, text: str) -> ChatMessage:
        if chat.title in {"", "New conversation"}:
            chat.title = auto_title(text)
        return await self.messages.append(
            chat,
            role="user",
            content=StoredMessage(parts=[StoredTextPart(text=text)]).model_dump(),
        )

    async def append_assistant(self, chat: ChatSession, turn: LLMMessage) -> ChatMessage:
        parts: list[StoredTextPart | StoredToolPart] = []
        if turn.text:
            parts.append(StoredTextPart(text=turn.text))
        for call in turn.tool_calls:
            parts.append(StoredToolPart(call_id=call.id, name=call.name, args=call.args))
        content = StoredMessage(parts=parts, raw=GeminiClient.serialize_raw(turn.raw)).model_dump()
        return await self.messages.append(chat, role="assistant", content=content, model=turn.model)

    async def append_tool(
        self, chat: ChatSession, calls_and_outcomes: list[tuple[str, str, dict, ToolOutcome]]
    ) -> ChatMessage:
        parts = []
        for call_id, name, args, outcome in calls_and_outcomes:
            pending = outcome.pending_revision or {}
            parts.append(
                StoredToolPart(
                    call_id=call_id,
                    name=name,
                    args=args,
                    ok=outcome.ok,
                    result=outcome.summary,
                    model_result=outcome.result
                    if outcome.ok
                    else {"ok": False, "error": outcome.error or "tool failed"},
                    error=outcome.error,
                    pending_revision_id=pending.get("id"),
                    pending_revision_status=pending.get("status"),
                    untrusted=outcome.untrusted,
                )
            )
        return await self.messages.append(chat, role="tool", content=StoredMessage(parts=parts).model_dump())
