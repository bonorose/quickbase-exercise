#!/usr/bin/env python3
# ******************************************************************************
# * @file    pending_revision_service.py
# * @author  Simeon Marlokov
# * @brief   Draft state machine. execute() is the only writer of tickets and
# *          revisions.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, ForbiddenError, GoneError, NotFoundError
from src.core.organization import OrganizationContext
from src.models.chat_message import ChatMessage
from src.models.pending_revision import PendingRevision
from src.models.revision import Revision
from src.models.ticket import Ticket, TicketPriority, TicketStatus
from src.models.user import User
from src.repositories.audit_repository import AuditRepository
from src.repositories.chat_session_repository import ChatSessionRepository
from src.repositories.discussion_repository import DiscussionRepository
from src.repositories.pending_revision_repository import PendingRevisionRepository
from src.repositories.revision_repository import RevisionRepository
from src.repositories.ticket_repository import TicketRepository
from src.schemas.chat.storage import StoredMessage, StoredTextPart
from src.schemas.pending_revisions.request import ChangedContents
from src.schemas.pending_revisions.response import merge_contents, present_pending, present_summary, snapshot

AGENT_DRAFT_TTL = timedelta(minutes=10)
LIST_LIMIT = 100
UNIQUE_VIOLATION = "23505"


@dataclass
class ProposeResult:
    draft: PendingRevision | None = None
    ticket: Ticket | None = None
    blocked_by: str | None = None


class PendingRevisionService:
    def __init__(
        self,
        drafts: PendingRevisionRepository,
        tickets: TicketRepository,
        revisions: RevisionRepository,
        discussions: DiscussionRepository,
        chats: ChatSessionRepository,
        audit: AuditRepository,
        organization: OrganizationContext,
        session: AsyncSession,
    ):
        self.drafts = drafts
        self.tickets = tickets
        self.revisions = revisions
        self.discussions = discussions
        self.chats = chats
        self.audit = audit
        self.organization = organization
        self.session = session

    async def expire_due(self) -> int:
        """Mark untouched agent drafts past their deadline. Tests call this directly."""
        now = datetime.now(UTC)
        due = list(await self.drafts.lock_due(now))
        if not due:
            return 0
        for draft in due:
            await self._mark_expired(draft, now)
        await self._commit()
        return len(due)

    async def open_summary(self, ticket_id: int):
        await self.expire_due()
        draft = await self.drafts.open_for_ticket(ticket_id)
        if draft is None:
            return None
        return present_summary(draft)

    async def claim(self, ticket_id: int, action: str, changed: ChangedContents | None) -> dict[str, Any]:
        await self.expire_due()
        ticket = await self.tickets.get_visible(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        existing = await self.drafts.lock_open_for_ticket(ticket_id)
        if existing is not None:
            raise self._worked_on(existing)
        now = datetime.now(UTC)
        draft = PendingRevision(
            ticket_id=ticket.id,
            organization_id=self.organization.organization_id,
            user_id=self.organization.user_id,
            previous_revision_id=await self.revisions.latest_id(ticket.id),
            changed_contents=self._partial(changed),
            action=action,
            status="open",
            tainted=False,
            expires_at=None,
            origin="human",
            session_id=None,
            date_updated=now,
        )
        self.session.add(draft)
        try:
            await self.session.flush()
            self._audit("user", "pending_revision_created", draft, self._meta(draft))
            await self._commit()
        except IntegrityError as exc:
            await self._conflict_from_integrity(ticket_id, exc)
        except ConflictError:
            existing = await self.drafts.open_for_ticket(ticket_id)
            if existing is None:
                raise
            raise self._worked_on(existing) from None
        return await self._present(draft.id)

    async def save(self, draft_id: uuid.UUID, changed: ChangedContents, action: str | None) -> dict[str, Any]:
        draft = await self._open_for_edit(draft_id)
        if draft.user_id != self.organization.user_id:
            raise ForbiddenError("Only the owner can save this pending revision")
        merged = dict(draft.changed_contents or {})
        merged.update(self._partial(changed))
        draft.changed_contents = merged
        if action is not None:
            draft.action = action
        draft.expires_at = None
        draft.previous_revision_id = await self.revisions.latest_id(draft.ticket_id)
        draft.date_updated = datetime.now(UTC)
        self._audit("user", "pending_revision_saved", draft, self._meta(draft))
        await self._commit()
        return await self._present(draft.id)

    async def approve(
        self, draft_id: uuid.UUID, changed: ChangedContents | None, action: str | None
    ) -> tuple[dict[str, Any], Ticket, list, list]:
        draft = await self._open_for_edit(draft_id)
        if draft.tainted and self.organization.role != "team_lead":
            raise ForbiddenError("A tainted pending revision can only be approved by a team lead")
        if not draft.tainted and draft.user_id != self.organization.user_id:
            raise NotFoundError(f"Pending revision {draft_id} not found")
        partial = dict(draft.changed_contents or {})
        partial.update(self._partial(changed))
        next_action = action or draft.action
        latest = await self.revisions.latest_id(draft.ticket_id)
        if draft.previous_revision_id != latest:
            raise ConflictError("Ticket changed since this draft was saved")
        ticket = await self.tickets.lock_visible(draft.ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {draft.ticket_id} not found")
        initial = snapshot(ticket)
        applied = merge_contents(initial, partial)
        now = datetime.now(UTC)
        revision = Revision(
            id=uuid.uuid4(),
            ticket_id=ticket.id,
            organization_id=self.organization.organization_id,
            user_id=self.organization.user_id,
            initial_contents=initial,
            changed_contents=applied,
        )
        self.session.add(revision)
        ticket.title = applied["title"]
        ticket.contents = applied["contents"]
        ticket.status = TicketStatus[applied["status"]].value
        ticket.priority = TicketPriority[applied["priority"]].value
        ticket.updated_by = self.organization.user_id
        if next_action == "delete":
            ticket.date_deleted = now
        draft.changed_contents = partial
        draft.action = next_action
        draft.status = "executed"
        draft.decided_by = self.organization.user_id
        draft.decided_at = now
        draft.date_updated = now
        draft.expires_at = None
        draft.result = {"revision_id": str(revision.id)}
        if next_action == "delete":
            draft.result["ticket_id"] = ticket.id
        await self._note(draft, "executed", await self._actor_name())
        self._audit("user", "pending_revision_approved", draft, self._meta(draft))
        self._audit(
            "user",
            "ticket_mutated",
            draft,
            {"revision_id": str(revision.id), "action": next_action},
        )
        await self._commit()
        presented = await self._present(draft.id)
        reloaded = await self.tickets.get_any(ticket.id)
        revisions = list(await self.revisions.list_for_ticket(ticket.id))
        discussions = list(await self.discussions.list_for_ticket(ticket.id))
        return presented, reloaded or ticket, revisions, discussions

    async def reject(self, draft_id: uuid.UUID, reason: str | None) -> dict[str, Any]:
        draft = await self._open_for_edit(draft_id)
        now = datetime.now(UTC)
        draft.status = "rejected"
        draft.decided_by = self.organization.user_id
        draft.decided_at = now
        draft.date_updated = now
        draft.expires_at = None
        draft.result = {"reason": reason} if reason else {}
        await self._note(draft, "rejected", await self._actor_name())
        self._audit("user", "pending_revision_rejected", draft, self._meta(draft))
        await self._commit()
        return await self._present(draft.id)

    async def get(self, draft_id: uuid.UUID) -> dict[str, Any]:
        await self.expire_due()
        draft = await self.drafts.get_loaded(draft_id)
        if draft is None or not self._visible(draft):
            raise NotFoundError(f"Pending revision {draft_id} not found")
        return await self._present_draft(draft)

    async def list_drafts(
        self,
        *,
        status: str,
        ticket_id: int | None,
        session_id: uuid.UUID | None,
        scope: str,
    ) -> list[dict[str, Any]]:
        await self.expire_due()
        if scope == "lead_queue":
            if self.organization.role != "team_lead":
                raise ForbiddenError("Team lead role is required")
            rows = await self.drafts.list_matching(
                user_id=None,
                status="open",
                ticket_id=ticket_id,
                session_id=session_id,
                tainted=True,
                limit=LIST_LIMIT,
            )
        else:
            rows = await self.drafts.list_matching(
                user_id=self.organization.user_id,
                status=None if status == "all" else status,
                ticket_id=ticket_id,
                session_id=session_id,
                tainted=None,
                limit=LIST_LIMIT,
            )
        return [await self._present_draft(row) for row in rows]

    async def propose(
        self,
        *,
        ticket_id: int,
        action: str,
        fields: dict[str, Any],
        tainted: bool,
        session_id: uuid.UUID,
    ) -> ProposeResult:
        await self.expire_due()
        ticket = await self.tickets.get_visible(ticket_id)
        if ticket is None:
            return ProposeResult()
        partial = {key: value for key, value in fields.items() if value is not None and key in {"status", "priority"}}
        existing = await self.drafts.lock_open_for_ticket(ticket_id)
        now = datetime.now(UTC)
        if existing is not None:
            if existing.user_id != self.organization.user_id:
                return ProposeResult(ticket=ticket, blocked_by=existing.owner.name)
            merged = dict(existing.changed_contents or {})
            merged.update(partial)
            existing.changed_contents = merged
            existing.action = action
            existing.tainted = bool(existing.tainted or tainted)
            existing.date_updated = now
            if existing.session_id is None:
                existing.session_id = session_id
            self._audit("agent", "pending_revision_saved", existing, self._meta(existing))
            await self._commit()
            return ProposeResult(draft=await self.drafts.get_loaded(existing.id), ticket=ticket)
        draft = PendingRevision(
            ticket_id=ticket.id,
            organization_id=self.organization.organization_id,
            user_id=self.organization.user_id,
            previous_revision_id=await self.revisions.latest_id(ticket.id),
            changed_contents=partial,
            action=action,
            status="open",
            tainted=tainted,
            expires_at=now + AGENT_DRAFT_TTL,
            origin="agent",
            session_id=session_id,
            date_updated=now,
        )
        self.session.add(draft)
        try:
            await self.session.flush()
            self._audit("agent", "pending_revision_created", draft, self._meta(draft))
            await self._commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if getattr(exc.orig, "sqlstate", None) != UNIQUE_VIOLATION:
                raise
            winner = await self.drafts.open_for_ticket(ticket_id)
            name = winner.owner.name if winner is not None else "someone"
            return ProposeResult(ticket=ticket, blocked_by=name)
        return ProposeResult(draft=await self.drafts.get_loaded(draft.id), ticket=ticket)

    async def _open_for_edit(self, draft_id: uuid.UUID) -> PendingRevision:
        await self.expire_due()
        draft = await self.drafts.lock(draft_id)
        if draft is None or not self._visible(draft):
            raise NotFoundError(f"Pending revision {draft_id} not found")
        await self._ensure_open(draft)
        return draft

    async def _ensure_open(self, draft: PendingRevision) -> None:
        now = datetime.now(UTC)
        expired = draft.status == "expired" or (
            draft.status == "open" and draft.expires_at is not None and draft.expires_at <= now
        )
        if expired:
            if draft.status == "open":
                await self._mark_expired(draft, now)
                await self._commit()
            raise GoneError("Pending revision has expired")
        if draft.status != "open":
            raise ConflictError("Pending revision is not open")

    async def _mark_expired(self, draft: PendingRevision, now: datetime) -> None:
        draft.status = "expired"
        draft.decided_at = now
        draft.date_updated = now
        await self._note(draft, "expired", "system")
        self.audit.stage(
            actor_type="system",
            event="pending_revision_expired",
            session_id=draft.session_id,
            ticket_id=draft.ticket_id,
            pending_revision_id=draft.id,
            payload=self._meta(draft),
        )

    async def _note(self, draft: PendingRevision, verb: str, name: str) -> None:
        if draft.session_id is None:
            return
        chat = await self.chats.get_in_organization(draft.session_id)
        if chat is None:
            return
        text = f"Pending revision {draft.id} was {verb} by {name}"
        self.session.add(
            ChatMessage(
                session_id=chat.id,
                organization_id=self.organization.organization_id,
                role="system",
                content=StoredMessage(parts=[StoredTextPart(text=text)]).model_dump(),
            )
        )
        chat.last_activity_at = datetime.now(UTC)

    def _visible(self, draft: PendingRevision) -> bool:
        if draft.user_id == self.organization.user_id:
            return True
        return self.organization.role == "team_lead" and draft.tainted

    def _worked_on(self, draft: PendingRevision) -> ConflictError:
        return ConflictError(
            f"being worked on by {draft.owner.name}",
            pending_revision_id=str(draft.id),
            owner={"id": draft.owner.id, "name": draft.owner.name},
        )

    async def _conflict_from_integrity(self, ticket_id: int, exc: IntegrityError) -> None:
        await self.session.rollback()
        if getattr(exc.orig, "sqlstate", None) != UNIQUE_VIOLATION:
            raise exc
        existing = await self.drafts.open_for_ticket(ticket_id)
        if existing is None:
            raise ConflictError("Pending revision conflicts with an existing record") from exc
        raise self._worked_on(existing) from exc

    async def _present(self, draft_id: uuid.UUID) -> dict[str, Any]:
        draft = await self.drafts.get_loaded(draft_id)
        if draft is None:
            raise NotFoundError(f"Pending revision {draft_id} not found")
        return await self._present_draft(draft)

    async def _present_draft(self, draft: PendingRevision) -> dict[str, Any]:
        ticket = await self.tickets.get_any(draft.ticket_id)
        return present_pending(draft, ticket)

    async def _actor_name(self) -> str:
        user = await self.session.get(User, self.organization.user_id)
        return user.name if user is not None else "someone"

    def _audit(self, actor_type: str, event: str, draft: PendingRevision, payload: dict[str, Any]) -> None:
        self.audit.stage(
            actor_type=actor_type,
            actor_id=None if actor_type == "system" else self.organization.user_id,
            event=event,
            session_id=draft.session_id,
            ticket_id=draft.ticket_id,
            pending_revision_id=draft.id,
            payload=payload,
        )

    @staticmethod
    def _meta(draft: PendingRevision) -> dict[str, Any]:
        return {"action": draft.action, "origin": draft.origin, "tainted": draft.tainted}

    @staticmethod
    def _partial(changed: ChangedContents | None) -> dict[str, Any]:
        if changed is None:
            return {}
        return {key: value for key, value in changed.model_dump().items() if value is not None}

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if getattr(exc.orig, "sqlstate", None) == UNIQUE_VIOLATION:
                raise ConflictError("Pending revision conflicts with an existing record") from exc
            raise


def build_pending_revision_service(session: AsyncSession, organization: OrganizationContext) -> PendingRevisionService:
    return PendingRevisionService(
        PendingRevisionRepository(session, organization),
        TicketRepository(session, organization),
        RevisionRepository(session, organization),
        DiscussionRepository(session, organization),
        ChatSessionRepository(session, organization),
        AuditRepository(session, organization),
        organization,
        session,
    )
