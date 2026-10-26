from datetime import UTC, datetime

from src.core.revocation_purge import seconds_until_utc_hour


def test_next_purge_is_later_the_same_day():
    now = datetime(2026, 10, 26, 1, 0, tzinfo=UTC)
    assert seconds_until_utc_hour(2, now) == 3600


def test_next_purge_rolls_to_the_following_day():
    now = datetime(2026, 10, 26, 3, 0, tzinfo=UTC)
    assert seconds_until_utc_hour(2, now) == 23 * 3600
