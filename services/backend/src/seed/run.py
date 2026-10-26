#!/usr/bin/env python3
# ******************************************************************************
# * @file    run.py
# * @author  Simeon Marlokov
# * @brief   Idempotent dev seed. Loads fixtures/qai_seed.json (see
# *          docs/seed/SEED_SCENARIO.md) through the owner connection, so RLS
# *          does not apply. Existing rows are left in place; on an empty
# *          database every ticket gets the id the fixture calls expected_id.
# * @date    26.10.2026
# ******************************************************************************
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.core.security import hash_password, verify_password
from src.models.discussion import Discussion
from src.models.organization import Organization
from src.models.pending_revision import PendingRevision
from src.models.revision import Revision
from src.models.ticket import Ticket
from src.models.user import User
from src.seed.data import load_seed, priority_value, status_value

TABLES = (
    "revoked_tokens",
    "audit_events",
    "pending_revisions",
    "chat_messages",
    "chat_sessions",
    "discussions",
    "revisions",
    "tickets",
    "users",
    "organizations",
)


async def seed(*, reset: bool = False) -> None:
    settings = get_settings()
    if settings.app_env == "production":
        raise SystemExit("Refusing to seed when APP_ENV=production")

    engine = create_async_engine(settings.migration_database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    password_hash = hash_password(settings.seed_user_password)
    try:
        async with factory() as session:
            if reset:
                await session.execute(text(f"TRUNCATE TABLE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
            created = await _apply(session, password_hash, settings.seed_user_password)
            await session.commit()
    finally:
        await engine.dispose()
    print(
        "Seed complete: "
        f"{created['organizations']} organizations, {created['users']} users, "
        f"{created['tickets']} tickets, {created['revisions']} revisions, "
        f"{created['pending_revisions']} pending revisions, {created['discussions']} discussions created "
        "(existing rows left in place)."
    )


def _moment(unix_seconds: int) -> datetime:
    return datetime.fromtimestamp(unix_seconds, tz=UTC)


async def _apply(session: AsyncSession, password_hash: str, password: str) -> dict[str, int]:
    fixture = load_seed()
    counts = {key: 0 for key in ("organizations", "users", "tickets", "revisions", "pending_revisions", "discussions")}

    organizations = await _organizations(session, fixture["organizations"], counts)
    users = await _users(session, fixture["users"], organizations, password_hash, password, counts)
    tickets = await _tickets(session, fixture["tickets"], organizations, users, counts)
    await _revisions(session, fixture["revisions"], tickets, users, counts)
    await _pending_revisions(session, fixture["pending_revisions"], tickets, users, counts)
    await _discussions(session, fixture["discussions"], tickets, users, counts)
    await session.flush()
    return counts


async def _organizations(
    session: AsyncSession, rows: list[dict[str, Any]], counts: dict[str, int]
) -> dict[str, Organization]:
    organizations: dict[str, Organization] = {}
    for row in rows:
        existing = await session.scalar(select(Organization).where(Organization.name == row["name"]))
        if existing is None:
            existing = Organization(name=row["name"])
            session.add(existing)
            await session.flush()
            counts["organizations"] += 1
        organizations[row["key"]] = existing
    return organizations


async def _users(
    session: AsyncSession,
    rows: list[dict[str, Any]],
    organizations: dict[str, Organization],
    password_hash: str,
    password: str,
    counts: dict[str, int],
) -> dict[str, User]:
    users: dict[str, User] = {}
    for row in rows:
        organization_id = organizations[row["organization"]].id
        existing = await session.scalar(select(User).where(func.lower(User.email) == row["email"].lower()))
        if existing is None:
            joined = date.fromisoformat(row["joined"])
            existing = User(
                email=row["email"],
                password_hash=password_hash,
                name=row["name"],
                organization_id=organization_id,
                role=row["role"],
                is_active=True,
                created_at=datetime(joined.year, joined.month, joined.day, 7, tzinfo=UTC),
            )
            session.add(existing)
            await session.flush()
            counts["users"] += 1
        else:
            # The seed owns the demo logins: keep name, role and team in line with the fixture,
            # and re-apply the password when SEED_USER_PASSWORD changed.
            existing.name = row["name"]
            existing.role = row["role"]
            existing.organization_id = organization_id
            if not verify_password(password, existing.password_hash):
                existing.password_hash = password_hash
        users[row["key"]] = existing
    return users


async def _tickets(
    session: AsyncSession,
    rows: list[dict[str, Any]],
    organizations: dict[str, Organization],
    users: dict[str, User],
    counts: dict[str, int],
) -> dict[str, Ticket]:
    """Inserted one by one, in file order, so that an empty table yields the fixture's expected_id."""
    tickets: dict[str, Ticket] = {}
    for row in rows:
        organization_id = organizations[row["organization"]].id
        created = _moment(row["date_created"])
        ticket = await session.scalar(
            select(Ticket).where(
                Ticket.organization_id == organization_id,
                Ticket.submitted_by == row["submitted_by"],
                Ticket.date_created == created,
            )
        )
        if ticket is None:
            ticket = Ticket(
                organization_id=organization_id,
                status=status_value(row["status"]),
                priority=priority_value(row["priority"]),
                title=row["title"],
                description=row["description"],
                contents=row["contents"],
                submitted_by=row["submitted_by"],
                updated_by=None if row["updated_by"] is None else users[row["updated_by"]].id,
                date_created=created,
                date_updated=_moment(row["date_updated"]),
            )
            session.add(ticket)
            await session.flush()
            counts["tickets"] += 1
        tickets[row["ref"]] = ticket
    return tickets


async def _revisions(
    session: AsyncSession,
    rows: list[dict[str, Any]],
    tickets: dict[str, Ticket],
    users: dict[str, User],
    counts: dict[str, int],
) -> None:
    wanted = [uuid.UUID(row["id"]) for row in rows]
    present = set((await session.scalars(select(Revision.id).where(Revision.id.in_(wanted)))).all())
    for row in rows:
        revision_id = uuid.UUID(row["id"])
        if revision_id in present:
            continue
        ticket = tickets[row["ticket_ref"]]
        session.add(
            Revision(
                id=revision_id,
                ticket_id=ticket.id,
                organization_id=ticket.organization_id,
                user_id=users[row["user"]].id,
                initial_contents=row["initial_contents"],
                changed_contents=row["changed_contents"],
                date_created=_moment(row["date_created"]),
            )
        )
        counts["revisions"] += 1
    await session.flush()


async def _pending_revisions(
    session: AsyncSession,
    rows: list[dict[str, Any]],
    tickets: dict[str, Ticket],
    users: dict[str, User],
    counts: dict[str, int],
) -> None:
    """Open human drafts: the tickets being worked on at the snapshot. One open draft per ticket."""
    ticket_ids = [tickets[row["ticket_ref"]].id for row in rows]
    busy = set(
        (
            await session.scalars(
                select(PendingRevision.ticket_id).where(
                    PendingRevision.ticket_id.in_(ticket_ids), PendingRevision.status == "open"
                )
            )
        ).all()
    )
    for row in rows:
        ticket = tickets[row["ticket_ref"]]
        if ticket.id in busy:
            continue
        previous = row.get("previous_revision_id")
        session.add(
            PendingRevision(
                ticket_id=ticket.id,
                organization_id=ticket.organization_id,
                user_id=users[row["user"]].id,
                previous_revision_id=None if previous is None else uuid.UUID(previous),
                changed_contents=row["changed_contents"],
                action=row["action"],
                status="open",
                tainted=False,
                expires_at=None,
                origin=row["origin"],
                session_id=None,
                date_created=_moment(row["date_created"]),
                date_updated=_moment(row["date_updated"]),
            )
        )
        busy.add(ticket.id)
        counts["pending_revisions"] += 1
    await session.flush()


async def _discussions(
    session: AsyncSession,
    rows: list[dict[str, Any]],
    tickets: dict[str, Ticket],
    users: dict[str, User],
    counts: dict[str, int],
) -> None:
    """The table has no date: rows are inserted in file order, which is chronological."""
    ticket_ids = {ticket.id for ticket in tickets.values()}
    present = set(
        (
            await session.execute(
                select(Discussion.ticket_id, Discussion.contents).where(Discussion.ticket_id.in_(ticket_ids))
            )
        ).all()
    )
    for row in rows:
        ticket = tickets[row["ticket_ref"]]
        key = (ticket.id, row["contents"])
        if key in present:
            continue
        session.add(
            Discussion(
                ticket_id=ticket.id,
                organization_id=ticket.organization_id,
                user_id=users[row["user"]].id,
                contents=row["contents"],
            )
        )
        present.add(key)
        counts["discussions"] += 1
    await session.flush()
