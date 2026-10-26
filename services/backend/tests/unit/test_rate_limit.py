import pytest

from src.core.organization import OrganizationContext
from src.core.output_safety import scrub_assistant_text
from src.core.rate_limit import MemoryRateLimiter, client_ip, enforce_write_limit

pytestmark = pytest.mark.unit


def test_blocked_call_does_not_extend_the_window():
    limiter = MemoryRateLimiter()
    assert limiter.allow("k", limit=1, window_seconds=60, now=0) is None
    retry = limiter.allow("k", limit=1, window_seconds=60, now=10)
    assert retry == 51
    assert limiter.allow("k", limit=1, window_seconds=60, now=10) == 51


def test_client_ip_ignores_forwarded_header_unless_the_peer_is_trusted(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXIES", "")
    from src.core.config import get_settings

    get_settings.cache_clear()
    assert client_ip("10.0.0.8", "203.0.113.5") == "10.0.0.8"
    monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.8")
    get_settings.cache_clear()
    assert client_ip("10.0.0.8", "203.0.113.5, 10.0.0.8") == "203.0.113.5"
    assert client_ip("10.0.0.9", "203.0.113.5") == "10.0.0.9"


def test_user_bucket_denial_does_not_count_an_organization_hit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_USER_PER_MINUTE", "1")
    monkeypatch.setenv("RATE_LIMIT_ORGANIZATION_PER_MINUTE", "2")
    from src.core.config import get_settings
    from src.core.rate_limit import get_rate_limiter

    get_settings.cache_clear()
    limiter = get_rate_limiter()
    limiter.reset()
    org = OrganizationContext(organization_id=7, user_id=3, role="operator")
    enforce_write_limit(org)
    with pytest.raises(Exception, match="Too many requests"):
        enforce_write_limit(org)
    other = OrganizationContext(organization_id=7, user_id=4, role="operator")
    enforce_write_limit(other)


def test_scrub_removes_markdown_images_and_raw_urls():
    raw = "See ![x](https://evil.example/exfil.png) and http://evil.example/a?q=1 now"
    assert scrub_assistant_text(raw) == "See [image removed] and [link removed] now"
    assert scrub_assistant_text("plain") == "plain"


def test_dockerignore_keeps_env_files_out_of_the_image():
    text = (__import__("pathlib").Path(__file__).resolve().parents[2] / ".dockerignore").read_text(encoding="utf-8")
    assert ".env" in text.splitlines()
    assert ".env.*" in text.splitlines()
