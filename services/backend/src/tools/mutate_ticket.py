#!/usr/bin/env python3
# ******************************************************************************
# * @file    tools/mutate_ticket.py
# * @author  Simeon Marlokov
# * @brief   Draft a status, priority, or deletion. Never writes the ticket.
# * @date    25.10.2026
# ******************************************************************************
from typing import Literal

from pydantic import Field

from src.schemas.pending_revisions.response import present_pending
from src.services.pending_revision_service import PendingRevisionService
from src.tools.base import Tool, ToolArgs, ToolContext, ToolOutcome

NOT_FOUND = "Ticket not found"


class MutateFields(ToolArgs):
    status: Literal["open", "blocked", "closed"] | None = None
    priority: Literal["lowest", "low", "medium", "high", "critical"] | None = None


class MutateTicketArgs(ToolArgs):
    id: int = Field(ge=1)
    action: Literal["update", "delete"]
    fields: MutateFields | None = None


class MutateTicketTool(Tool):
    name = "mutate_ticket"
    description = (
        "Propose a status or priority change, or a deletion, for one ticket in the signed-in "
        "operator's organization. This creates a draft and does not change the ticket."
    )
    args_model = MutateTicketArgs
    kind = "mutate"

    def __init__(self, drafts: PendingRevisionService):
        self.drafts = drafts

    async def run(self, args: ToolArgs, ctx: ToolContext) -> ToolOutcome:
        parsed = args if isinstance(args, MutateTicketArgs) else MutateTicketArgs.model_validate(args)
        fields = {} if parsed.fields is None else parsed.fields.model_dump()
        outcome = await self.drafts.propose(
            ticket_id=parsed.id,
            action=parsed.action,
            fields=fields,
            tainted=ctx.turn_tainted,
            session_id=ctx.session_id,
        )
        if outcome.ticket is None or outcome.draft is None:
            if outcome.blocked_by:
                return ToolOutcome(ok=False, error=f"being worked on by {outcome.blocked_by}")
            return ToolOutcome(ok=False, error=NOT_FOUND)
        body = present_pending(outcome.draft, outcome.ticket)
        summary = {"pending_revision_id": body["id"], "status": body["status"]}
        return ToolOutcome(ok=True, result=summary, summary=summary, pending_revision=body)
