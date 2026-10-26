#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat_service.py
# * @author  Simeon Marlokov
# * @brief   Chat sessions and the C-20 stream. The stream uses its own database
# *          session so a client disconnect can still commit finished turns.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from collections.abc import AsyncIterator

from loguru import logger

from src.core.exceptions import NotFoundError, ServiceUnavailableError
from src.db.session import bind_organization, get_session_factory
from src.integrations.llm.types import LLMClient, LLMQuotaExhaustedError, LLMUnavailableError
from src.models.chat_session import ChatSession
from src.repositories.audit_repository import AuditRepository
from src.repositories.chat_message_repository import ChatMessageRepository
from src.repositories.chat_session_repository import ChatSessionRepository
from src.repositories.discussion_repository import DiscussionRepository
from src.repositories.revision_repository import RevisionRepository
from src.repositories.ticket_repository import TicketRepository
from src.schemas.chat.stream import (
    ApprovalRequiredStreamEvent,
    ChatStreamEvent,
    DeltaStreamEvent,
    DoneStreamEvent,
    ErrorStreamEvent,
    SessionStreamEvent,
    StatusStreamEvent,
    ToolCallStreamEvent,
    ToolResultStreamEvent,
)
from src.services.agent.agent_service import AgentService
from src.services.agent.events import (
    AgentApprovalRequired,
    AgentDelta,
    AgentDone,
    AgentModelTurn,
    AgentStatus,
    AgentToolCall,
    AgentToolResult,
)
from src.services.agent.history import HistoryStore
from src.services.pending_revision_service import build_pending_revision_service
from src.services.ticket_service import TicketService
from src.tools.base import ToolContext
from src.tools.mutate_ticket import MutateTicketTool
from src.tools.registry import ToolRegistry
from src.tools.search_tickets import SearchTicketsTool

DEFAULT_TITLE = "New conversation"


class ChatService:
    def __init__(
        self,
        sessions: ChatSessionRepository,
        messages: ChatMessageRepository,
        client: LLMClient | None,
        *,
        max_iterations: int,
        history_limit: int,
        tools: list | None = None,
    ):
        self.sessions = sessions
        self.messages = messages
        self.client = client
        self.max_iterations = max_iterations
        self.history_limit = history_limit
        self.tools = tools
        self.organization = sessions.organization

    async def create_session(self, title: str | None) -> ChatSession:
        cleaned = (title or "").strip()
        return await self.sessions.create_session(cleaned or DEFAULT_TITLE)

    async def list_sessions(self, limit: int, offset: int) -> tuple[list[ChatSession], int]:
        return list(await self.sessions.list_for_user(limit, offset)), await self.sessions.count_for_user()

    async def get_session(self, session_id: uuid.UUID) -> tuple[ChatSession, list]:
        chat = await self.sessions.get_owned(session_id)
        if chat is None:
            raise NotFoundError(f"Chat session {session_id} not found")
        return chat, list(await self.messages.list_for_session(chat.id))

    async def pending_statuses(self, ids: list[str]) -> dict[str, str]:
        parsed: list[uuid.UUID] = []
        for item in ids:
            try:
                parsed.append(uuid.UUID(item))
            except ValueError:
                continue
        if not parsed:
            return {}
        service = build_pending_revision_service(self.messages.session, self.organization)
        await service.expire_due()
        return await service.drafts.statuses(parsed)

    async def open_stream(self, session_id: uuid.UUID) -> ChatSession:
        """Fail before the response starts. A missing session and a missing model are not SSE."""
        chat = await self.sessions.get_owned(session_id)
        if chat is None:
            raise NotFoundError(f"Chat session {session_id} not found")
        if self.client is None:
            raise ServiceUnavailableError("The LLM is not configured.")
        return chat

    def stream_message(self, session_id: uuid.UUID, text: str) -> AsyncIterator[ChatStreamEvent]:
        if self.client is None:
            raise ServiceUnavailableError("The LLM is not configured.")
        return self._stream(session_id, text, self.client)

    async def _stream(self, session_id: uuid.UUID, text: str, client: LLMClient) -> AsyncIterator[ChatStreamEvent]:
        factory = get_session_factory()
        async with factory() as db:
            await bind_organization(db, self.organization.organization_id)
            sessions = ChatSessionRepository(db, self.organization)
            messages = ChatMessageRepository(db, self.organization)
            chat = await sessions.get_owned(session_id)
            if chat is None:
                raise NotFoundError(f"Chat session {session_id} not found")
            history = HistoryStore(messages, self.history_limit)
            prior, session_tainted = await history.load_for_turn(chat.id)
            await history.append_user(chat, text)
            tickets = TicketService(
                TicketRepository(db, self.organization),
                RevisionRepository(db, self.organization),
                DiscussionRepository(db, self.organization),
            )
            drafts = build_pending_revision_service(db, self.organization)
            registry = ToolRegistry(self.tools or [SearchTicketsTool(tickets), MutateTicketTool(drafts)])
            audit = AuditRepository(db, self.organization)
            agent = AgentService(client, registry, self.max_iterations)
            # A draft is tainted if untrusted text reached the model in this turn or any earlier one.
            ctx = ToolContext(organization=self.organization, session_id=chat.id, db=db, turn_tainted=session_tainted)
            yield SessionStreamEvent(session_id=str(chat.id))
            pending_turn = None
            outcomes: list[tuple[str, str, dict, object]] = []
            try:
                async for event in agent.run_turn(ctx, prior, text):
                    match event:
                        case AgentStatus(message=message):
                            yield StatusStreamEvent(message=message)
                        case AgentDelta(text=delta):
                            yield DeltaStreamEvent(text=delta)
                        case AgentModelTurn(turn=turn):
                            await history.append_assistant(chat, turn)
                            pending_turn = turn
                            outcomes = []
                        case AgentToolCall(call=call):
                            yield ToolCallStreamEvent(call_id=call.id, name=call.name, args=call.args)
                        case AgentToolResult(call_id=call_id, outcome=outcome):
                            call = next(
                                item for item in (pending_turn.tool_calls if pending_turn else ()) if item.id == call_id
                            )
                            outcomes.append((call.id, call.name, call.args, outcome))
                            if pending_turn is not None and len(outcomes) == len(pending_turn.tool_calls):
                                for _call_id, name, args, recorded in outcomes:
                                    ticket_id = args.get("id") if isinstance(args.get("id"), int) else None
                                    pending_id = None
                                    if recorded.pending_revision and recorded.pending_revision.get("id"):
                                        pending_id = uuid.UUID(str(recorded.pending_revision["id"]))
                                    audit.stage(
                                        actor_type="agent",
                                        actor_id=self.organization.user_id,
                                        event="tool_called",
                                        session_id=chat.id,
                                        ticket_id=ticket_id,
                                        pending_revision_id=pending_id,
                                        payload={"name": name, "ok": recorded.ok},
                                    )
                                await history.append_tool(chat, outcomes)  # type: ignore[arg-type]
                                pending_turn = None
                                outcomes = []
                            yield ToolResultStreamEvent(
                                call_id=call_id,
                                ok=outcome.ok,
                                result=outcome.summary,
                                error=outcome.error,
                            )
                        case AgentApprovalRequired(call_id=call_id, pending_revision=pending):
                            yield ApprovalRequiredStreamEvent(call_id=call_id, pending_revision=pending)
                        case AgentDone(model=model, turn=turn):
                            saved = await history.append_assistant(chat, turn)
                            yield DoneStreamEvent(message_id=str(saved.id), model=model)
            except LLMQuotaExhaustedError as exc:
                yield ErrorStreamEvent(message=str(exc), code="quota_exhausted")
            except LLMUnavailableError as exc:
                yield ErrorStreamEvent(message=str(exc), code="llm_unavailable")
            except Exception:
                logger.exception("Chat stream failed")
                yield ErrorStreamEvent(message="Something went wrong while answering.", code="internal")
