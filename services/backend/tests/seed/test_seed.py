import os

import pytest
from sqlalchemy import text

from src.core.config import get_settings
from src.seed.data import ADVERSARIAL_TECHNIQUES, adversarial_tickets, load_seed
from src.seed.run import seed

pytestmark = pytest.mark.api


async def _counts(owner_engine) -> dict[str, int]:
    async with owner_engine.connect() as connection:
        counts = {}
        for table in ("organizations", "users", "tickets", "revisions", "pending_revisions", "discussions"):
            counts[table] = await connection.scalar(text(f"SELECT count(*) FROM {table}"))  # noqa: S608
        return counts


async def test_seed_is_idempotent_and_matches_the_fixture(owner_engine):
    fixture = load_seed()
    await seed()
    first = await _counts(owner_engine)
    await seed()
    second = await _counts(owner_engine)
    assert first == second
    assert first["organizations"] == len(fixture["organizations"]) == 2
    assert first["users"] == len(fixture["users"]) == 13
    assert first["tickets"] == len(fixture["tickets"])
    assert first["revisions"] == len(fixture["revisions"])
    assert first["pending_revisions"] == len(fixture["pending_revisions"])
    assert first["discussions"] == len(fixture["discussions"])


async def test_seed_ids_follow_the_fixture_on_an_empty_database(owner_engine):
    fixture = load_seed()
    await seed(reset=True)
    async with owner_engine.connect() as connection:
        rows = (
            await connection.execute(
                text(
                    "SELECT t.id, o.name, t.title, t.status, t.priority, t.contents, "
                    "extract(epoch FROM t.date_created)::bigint "
                    "FROM tickets t JOIN organizations o ON o.id = t.organization_id ORDER BY t.id"
                )
            )
        ).all()
    by_key = {organization["key"]: organization["name"] for organization in fixture["organizations"]}
    assert [row[0] for row in rows] == [ticket["expected_id"] for ticket in fixture["tickets"]]
    for row, ticket in zip(rows, fixture["tickets"], strict=True):
        assert row[1] == by_key[ticket["organization"]]
        assert row[2] == ticket["title"]
        assert row[6] == ticket["date_created"]
    # The fake model's script and the E2E suite draft on ticket #1: an open Excellence ticket about billing.
    assert rows[0][1] == "Excellence"
    assert rows[0][3] == 1
    assert "billing" in rows[0][5]


async def test_seed_keeps_revisions_consistent_with_tickets(owner_engine):
    await seed(reset=True)
    async with owner_engine.connect() as connection:
        mismatched = await connection.scalar(
            text(
                """
                SELECT count(*) FROM tickets t
                JOIN LATERAL (
                    SELECT changed_contents FROM revisions r
                    WHERE r.ticket_id = t.id ORDER BY r.date_created DESC LIMIT 1
                ) last ON true
                WHERE last.changed_contents->>'title' <> t.title
                   OR last.changed_contents->>'contents' <> t.contents
                """
            )
        )
        foreign = await connection.scalar(
            text(
                """
                SELECT count(*) FROM revisions r JOIN tickets t ON t.id = r.ticket_id
                JOIN users u ON u.id = r.user_id
                WHERE u.organization_id <> t.organization_id OR r.organization_id <> t.organization_id
                """
            )
        )
        open_drafts = await connection.scalar(
            text(
                "SELECT count(*) FROM pending_revisions p JOIN tickets t ON t.id = p.ticket_id "
                "WHERE p.status = 'open' AND p.origin = 'human' AND t.status <> 3"
            )
        )
        total_drafts = await connection.scalar(text("SELECT count(*) FROM pending_revisions"))
    assert mismatched == 0
    assert foreign == 0
    assert open_drafts == total_drafts == len(load_seed()["pending_revisions"])


async def test_seed_contains_the_adversarial_tickets(owner_engine):
    await seed(reset=True)
    adversarial = adversarial_tickets()
    assert len(adversarial) == 8
    assert {ticket["adversarial"]["technique"] for ticket in adversarial} == ADVERSARIAL_TECHNIQUES
    async with owner_engine.connect() as connection:
        for ticket in adversarial:
            row = (
                await connection.execute(
                    text("SELECT contents, description, organization_id FROM tickets WHERE id = :id"),
                    {"id": ticket["expected_id"]},
                )
            ).one()
            assert row[0] == ticket["contents"]
            assert row[1] == ticket["description"]
            target = ticket["adversarial"].get("target_ticket_id")
            if target is not None:
                other = await connection.scalar(
                    text("SELECT organization_id FROM tickets WHERE id = :id"), {"id": target}
                )
                assert other is not None and other != row[2], "the payload must point at the other team's ticket"
    payloads = "\n".join(ticket["contents"] for ticket in adversarial)
    assert "mutate_ticket with action=delete" in payloads
    assert "attacker.tld" in payloads
    assert "organization_id" in payloads


async def test_seed_refuses_production():
    os.environ["APP_ENV"] = "production"
    get_settings.cache_clear()
    try:
        with pytest.raises(SystemExit):
            await seed()
    finally:
        os.environ["APP_ENV"] = "local"
        get_settings.cache_clear()
