"""Drive a scenario through the HTTP API and snapshot the database."""

import json
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from evals.gates import evaluate_all
from evals.records import RunRecord, StepRecord, TicketRow, TrialResult
from evals.scenario import VariantModel, parse_gate
from src.core.config import get_settings
from src.integrations.llm import get_llm_client
from src.integrations.llm.fake import ScriptedLLMClient, ScriptedTurn, normalize_prompt
from src.integrations.llm.types import ToolCall


def relax_rate_limits() -> None:
    import os

    os.environ["RATE_LIMIT_USER_PER_MINUTE"] = "10000"
    os.environ["RATE_LIMIT_ORGANIZATION_PER_MINUTE"] = "10000"
    os.environ["RATE_LIMIT_LOGIN_EMAIL"] = "10000"
    os.environ["RATE_LIMIT_LOGIN_IP"] = "10000"
    get_settings.cache_clear()


class SuiteRunner:
    def __init__(self, client: httpx.AsyncClient, engine: AsyncEngine, app: Any):
        self.client = client
        self.engine = engine
        self.app = app
        self._tokens: dict[str, str] = {}
        self._world: dict[str, Any] | None = None

    async def world(self) -> dict[str, Any]:
        if self._world is None:
            self._world = await _load_world(self.engine)
        return self._world

    async def run_variant(
        self, scenario_id: str, actor_org: str, actor_email: str, variant: VariantModel, *, live: bool
    ) -> TrialResult:
        label = f"{scenario_id}/{variant.id}"
        from src.seed.run import seed

        await seed(reset=True)
        self._world = None
        self._tokens.clear()
        record = await self._execute(label, actor_org, actor_email, variant, live=live)
        if record.quota_exhausted:
            return TrialResult(label, True, [], _excerpt(record), quota_exhausted=True)
        failures = evaluate_all(record, [parse_gate(item) for item in variant.gates])
        return TrialResult(label, not failures, failures, _excerpt(record), quota_exhausted=record.quota_exhausted)

    async def _execute(
        self, label: str, actor_org: str, actor_email: str, variant: VariantModel, *, live: bool
    ) -> RunRecord:
        world = await self.world()
        own = world["ids"][actor_org]
        other_org = next(name for name in world["ids"] if name != actor_org)
        other = world["ids"][other_org]
        if not live:
            _install_script(self.app, variant, own, other)
        else:
            self.app.dependency_overrides.pop(get_llm_client, None)
        before_tickets, before_revisions, _ = await _snapshot(self.engine)
        foreign_ids, foreign_texts = _foreign_markers(world, actor_org)
        steps: list[StepRecord] = []
        session_id: str | None = None
        quota = False
        error: str | None = None
        try:
            token = await self._token(actor_email)
            for step in variant.steps:
                user = step.user or actor_email
                headers = {"Authorization": f"Bearer {await self._token(user)}"}
                if step.say:
                    if session_id is None:
                        created = await self.client.post(
                            "/api/v1/chat/sessions", json={}, headers={"Authorization": f"Bearer {token}"}
                        )
                        if created.status_code != 201:
                            raise RuntimeError(f"create session failed: {created.status_code} {created.text}")
                        session_id = created.json()["id"]
                    recorded = await self._say(session_id, step.say, {"Authorization": f"Bearer {token}"})
                elif step.decide:
                    recorded = await self._decide(step.decide, step.extra_body, step.from_step, steps, headers)
                elif step.save:
                    recorded = await self._save(step.from_step, steps, headers)
                elif step.expire:
                    await _expire_open_drafts(self.engine)
                    recorded = StepRecord("expire", 204)
                elif step.diverge:
                    draft = _require_draft(steps, step.from_step)
                    await _diverge(self.engine, int(draft["ticket"]["id"]))
                    recorded = StepRecord(
                        "diverge", 204, draft_id=str(draft["id"]), ticket_id=int(draft["ticket"]["id"])
                    )
                else:
                    raise RuntimeError("step has no action")
                steps.append(recorded)
                if any(event.get("code") == "quota_exhausted" for event in recorded.events):
                    quota = True
                    break
        except Exception as exc:
            error = str(exc)
        tickets, revisions, drafts = await _snapshot(self.engine)
        history = await self._history(session_id, actor_email) if session_id else ""
        return RunRecord(
            scenario_id=label,
            steps=steps,
            tickets_before=before_tickets,
            tickets_after=tickets,
            revision_ids_before=[item["id"] for item in before_revisions],
            revision_ids_after=[item["id"] for item in revisions],
            revisions_after=revisions,
            drafts_after=drafts,
            foreign_ticket_ids=foreign_ids,
            foreign_texts=foreign_texts,
            own_ticket_ids=set(own),
            history_text=history,
            quota_exhausted=quota,
            error=error,
        )

    async def _token(self, email: str) -> str:
        cached = self._tokens.get(email)
        if cached:
            return cached
        response = await self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": get_settings().seed_user_password},
        )
        if response.status_code != 200:
            raise RuntimeError(f"login failed for {email}: {response.status_code} {response.text}")
        token = response.json()["access_token"]
        self._tokens[email] = token
        return token

    async def _say(self, session_id: str, text_value: str, headers: dict[str, str]) -> StepRecord:
        async with self.client.stream(
            "POST",
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"text": text_value},
            headers=headers,
        ) as response:
            events = await _read_events(response)
            status_code = response.status_code
        draft = _draft_from(events)
        return StepRecord(
            "say",
            status_code,
            events,
            draft_id=None if draft is None else str(draft["id"]),
            ticket_id=None if draft is None else int(draft["ticket"]["id"]),
            draft=draft,
        )

    async def _decide(
        self,
        action: str,
        extra: dict[str, Any] | None,
        from_step: int | None,
        steps: list[StepRecord],
        headers: dict[str, str],
    ) -> StepRecord:
        draft = (
            _require_draft(steps, from_step)
            if _has_draft(steps, from_step)
            else {"id": "00000000-0000-0000-0000-000000000000", "ticket": {"id": 0}}
        )
        payload = dict(extra or {})
        response = await self.client.post(
            f"/api/v1/pending-revisions/{draft['id']}/{action}", json=payload, headers=headers
        )
        body: Any
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}
        return StepRecord(
            "decide",
            response.status_code,
            [],
            body,
            draft_id=str(draft["id"]),
            ticket_id=int(draft["ticket"]["id"]) or None,
            draft=draft,
        )

    async def _save(self, from_step: int | None, steps: list[StepRecord], headers: dict[str, str]) -> StepRecord:
        draft = _require_draft(steps, from_step)
        payload = {"changed_contents": draft.get("changed_contents") or {}, "action": draft.get("action") or "update"}
        response = await self.client.put(f"/api/v1/pending-revisions/{draft['id']}", json=payload, headers=headers)
        return StepRecord(
            "save", response.status_code, [], draft_id=str(draft["id"]), ticket_id=int(draft["ticket"]["id"])
        )

    async def _history(self, session_id: str, email: str) -> str:
        response = await self.client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers={"Authorization": f"Bearer {await self._token(email)}"},
        )
        if response.status_code != 200:
            return f"history status {response.status_code} {response.text[:200]}"
        chunks = []
        for message in response.json().get("messages") or []:
            for part in message.get("parts") or []:
                if part.get("text"):
                    chunks.append(str(part["text"]))
        return "\n".join(chunks)


def _install_script(app: Any, variant: VariantModel, own: list[int], other: list[int]) -> None:
    scripts: dict[str, ScriptedTurn] = {}
    for prompt, turn in variant.script.items():
        calls = [
            ToolCall(id=f"call-{index}", name=call.name, args=_resolve(call.args, own, other))
            for index, call in enumerate(turn.tool_calls)
        ]
        scripts[normalize_prompt(prompt)] = ScriptedTurn(tool_calls=calls, text=turn.text)
    client = ScriptedLLMClient(scripts)
    app.dependency_overrides[get_llm_client] = lambda: client


def _resolve(value: Any, own: list[int], other: list[int]) -> Any:
    if isinstance(value, str) and value.startswith("$self:"):
        return own[int(value.split(":", 1)[1])]
    if isinstance(value, str) and value.startswith("$other:"):
        return other[int(value.split(":", 1)[1])]
    if isinstance(value, dict):
        return {key: _resolve(item, own, other) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, own, other) for item in value]
    return value


async def _read_events(response: httpx.Response) -> list[dict[str, Any]]:
    if response.status_code != 200:
        raw = await response.aread()
        try:
            return [{"type": "error", "message": raw.decode(), "code": "internal"}]
        except Exception:
            return [{"type": "error", "message": "unreadable body", "code": "internal"}]
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line.removeprefix("data: ")))
    return events


def _draft_from(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("type") == "approval_required":
            draft = event.get("pending_revision")
            if isinstance(draft, dict):
                return draft
    return None


def _has_draft(steps: list[StepRecord], from_step: int | None) -> bool:
    if from_step is None:
        return any(step.draft for step in steps)
    return 0 <= from_step < len(steps) and steps[from_step].draft is not None


def _require_draft(steps: list[StepRecord], from_step: int | None) -> dict[str, Any]:
    if from_step is None:
        for step in reversed(steps):
            if step.draft:
                return step.draft
    elif 0 <= from_step < len(steps) and steps[from_step].draft:
        return steps[from_step].draft
    raise RuntimeError("no draft is available for this step")


async def _load_world(engine: AsyncEngine) -> dict[str, Any]:
    async with engine.connect() as connection:
        rows = (
            await connection.execute(
                text(
                    """
                    SELECT o.name, t.id, t.title, t.contents, d.contents
                    FROM tickets t
                    JOIN organizations o ON o.id = t.organization_id
                    LEFT JOIN discussions d ON d.ticket_id = t.id
                    ORDER BY t.id, d.id
                    """
                )
            )
        ).all()
    ids: dict[str, list[int]] = {}
    texts: dict[str, set[str]] = {}
    for org, ticket_id, title, contents, discussion in rows:
        bucket = ids.setdefault(org, [])
        if ticket_id not in bucket:
            bucket.append(ticket_id)
        texts.setdefault(org, set()).update(item for item in (title, contents, discussion) if item)
    return {"ids": ids, "texts": texts}


def _foreign_markers(world: dict[str, Any], actor_org: str) -> tuple[set[int], list[str]]:
    own_ids = set(world["ids"].get(actor_org, []))
    own_text = world["texts"].get(actor_org, set())
    foreign_ids = {ticket_id for org, bucket in world["ids"].items() if org != actor_org for ticket_id in bucket}
    foreign_ids -= own_ids
    foreign_texts = []
    for org, bucket in world["texts"].items():
        if org == actor_org:
            continue
        for item in bucket:
            if item not in own_text and len(item) >= 24:
                foreign_texts.append(item)
    return foreign_ids, foreign_texts


async def _snapshot(engine: AsyncEngine) -> tuple[list[TicketRow], list[dict[str, Any]], list[dict[str, Any]]]:
    async with engine.connect() as connection:
        tickets = (
            await connection.execute(
                text("SELECT id, organization_id, status, priority, title, contents FROM tickets ORDER BY id")
            )
        ).all()
        revisions = (
            await connection.execute(
                text("SELECT id::text, ticket_id, changed_contents FROM revisions ORDER BY date_created")
            )
        ).all()
        drafts = (
            await connection.execute(
                text(
                    "SELECT id::text, ticket_id, status, tainted, changed_contents "
                    "FROM pending_revisions ORDER BY date_created"
                )
            )
        ).all()
    return (
        [TicketRow(int(row[0]), int(row[1]), int(row[2]), int(row[3]), row[4], row[5]) for row in tickets],
        [{"id": row[0], "ticket_id": int(row[1]), "changed_contents": row[2]} for row in revisions],
        [
            {"id": row[0], "ticket_id": int(row[1]), "status": row[2], "tainted": row[3], "changed_contents": row[4]}
            for row in drafts
        ],
    )


async def _expire_open_drafts(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "UPDATE pending_revisions SET expires_at = now() - interval '1 minute' "
                "WHERE status = 'open' AND expires_at IS NOT NULL"
            )
        )


async def _diverge(engine: AsyncEngine, ticket_id: int) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                INSERT INTO revisions (id, ticket_id, organization_id, user_id, initial_contents, changed_contents)
                SELECT gen_random_uuid(), t.id, t.organization_id, u.id,
                       '{"title":"before","contents":"before","status":"open","priority":"low"}'::jsonb,
                       '{"title":"after","contents":"after","status":"open","priority":"high"}'::jsonb
                FROM tickets t
                JOIN users u ON u.organization_id = t.organization_id
                WHERE t.id = :ticket_id
                LIMIT 1
                """
            ),
            {"ticket_id": ticket_id},
        )


def _excerpt(record: RunRecord) -> str:
    lines = []
    for step in record.steps:
        detail = ""
        if isinstance(step.body, dict) and step.body.get("detail"):
            detail = f" {step.body['detail']}"
        tainted = "" if not step.draft else f" tainted={step.draft.get('tainted')}"
        lines.append(f"{step.kind} {step.status_code}{tainted}{detail}")
    if record.history_text:
        lines.append(f"history={record.history_text[:240]}")
    if record.error:
        lines.append(record.error)
    return "\n".join(lines)
