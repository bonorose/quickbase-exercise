import statistics
import time

import bcrypt
import pytest
from sqlalchemy import text
from tests.factories import commit_operator
from tests.helpers.auth import auth_header

from src.core.config import get_settings
from src.core.security import create_access_token, decode_access_token

pytestmark = pytest.mark.api

ORIGIN = {"Origin": "http://localhost:3000"}


async def test_livez_is_public_and_health_stays_authenticated(client, monkeypatch):
    def explode():
        raise RuntimeError("database should not be touched")

    monkeypatch.setattr("src.db.session.get_engine", explode)
    live = await client.get("/livez")
    assert live.status_code == 200
    assert live.json() == {"status": "ok"}
    health = await client.get("/health")
    assert health.status_code == 401
    schema = (await client.get("/openapi.json")).json()
    assert schema["paths"]["/livez"]["get"]["security"] == []
    health_security = schema["paths"]["/health"]["get"].get("security", schema["security"])
    assert health_security == [{"BearerAuth": []}]


async def test_unhandled_route_error_is_generic_and_cors_visible(client, owner_engine):
    await commit_operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    response = await client.get("/api/v1/__boom", headers={**headers, **ORIGIN})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "secret" not in response.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_auth_infrastructure_failure_is_generic_and_cors_visible(client, monkeypatch):
    def explode():
        raise RuntimeError("connection refused")

    monkeypatch.setattr("src.middlewares.auth.get_session_factory", explode)
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer x", **ORIGIN})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "connection refused" not in response.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.slow
async def test_unknown_email_takes_about_as_long_as_a_wrong_password(client, owner_engine, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_EMAIL", "100")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IP", "100")
    get_settings.cache_clear()
    await commit_operator(owner_engine, email="op1@excellence.qai.local")
    slow_hash = bcrypt.hashpw(b"password", bcrypt.gensalt(rounds=12)).decode()
    async with owner_engine.begin() as connection:
        await connection.execute(
            text("UPDATE users SET password_hash = :password_hash WHERE lower(email) = lower(:email)"),
            {"password_hash": slow_hash, "email": "op1@excellence.qai.local"},
        )

    async def samples(email: str) -> list[float]:
        timings = []
        for index in range(20):
            started = time.perf_counter()
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": email if "@" in email else f"missing-{index}@example.com", "password": "wrong-password"},
            )
            timings.append(time.perf_counter() - started)
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid email or password"
        return timings

    unknown = statistics.median(await samples("missing"))
    wrong = statistics.median(await samples("op1@excellence.qai.local"))
    assert abs(unknown - wrong) / max(unknown, wrong) < 0.20


async def test_login_rate_limit_uses_the_peer_and_sets_retry_after(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_EMAIL", "2")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IP", "100")
    get_settings.cache_clear()
    body = {"email": "nobody@example.com", "password": "nope"}
    assert (await client.post("/api/v1/auth/login", json=body)).status_code == 401
    assert (await client.post("/api/v1/auth/login", json=body)).status_code == 401
    blocked = await client.post("/api/v1/auth/login", json=body, headers=ORIGIN)
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Too many requests"}
    assert int(blocked.headers["retry-after"]) >= 1
    assert blocked.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_forwarded_for_is_ignored_until_the_proxy_is_trusted(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_EMAIL", "1")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IP", "1")
    monkeypatch.setenv("TRUSTED_PROXIES", "")
    get_settings.cache_clear()
    first = {"email": "a@example.com", "password": "nope"}
    second = {"email": "b@example.com", "password": "nope"}
    opened = await client.post("/api/v1/auth/login", json=first, headers={"X-Forwarded-For": "203.0.113.1"})
    assert opened.status_code == 401
    blocked = await client.post("/api/v1/auth/login", json=first, headers={"X-Forwarded-For": "203.0.113.2"})
    assert blocked.status_code == 429
    monkeypatch.setenv("TRUSTED_PROXIES", "127.0.0.1,testclient")
    get_settings.cache_clear()
    allowed = await client.post("/api/v1/auth/login", json=second, headers={"X-Forwarded-For": "203.0.113.9"})
    assert allowed.status_code == 401


async def test_login_sets_cookies_and_cookie_posts_require_csrf(client, owner_engine):
    await commit_operator(owner_engine)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "op1@excellence.qai.local", "password": "password"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
    raw = response.headers.get_list("set-cookie")
    session = next(item for item in raw if item.startswith("qb_session="))
    csrf = next(item for item in raw if item.startswith("qb_csrf="))
    assert "HttpOnly" in session
    assert "HttpOnly" not in csrf
    assert "Secure" not in session
    assert "SameSite=lax" in session
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    denied = await client.post("/api/v1/auth/logout")
    assert denied.status_code == 403
    assert denied.json()["detail"] == "CSRF check failed"
    csrf_value = client.cookies["qb_csrf"]
    logged_out = await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_value})
    assert logged_out.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_bearer_post_does_not_need_csrf_and_logout_revokes_only_that_jti(client, owner_engine):
    organization_id, user_id = await commit_operator(owner_engine)
    first = await client.post(
        "/api/v1/auth/login",
        json={"email": "op1@excellence.qai.local", "password": "password"},
    )
    client.cookies.clear()
    user = type("User", (), {"id": user_id, "organization_id": organization_id, "role": "operator"})()
    other_token, _ = create_access_token(user)
    token = first.json()["access_token"]
    logout = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 204
    assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})).status_code == 401
    assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {other_token}"})).status_code == 200
    async with owner_engine.connect() as connection:
        events = (
            (await connection.execute(text("SELECT event FROM audit_events WHERE event = 'logout'"))).scalars().all()
        )
    assert events == ["logout"]
    assert decode_access_token(token).jti != decode_access_token(other_token).jti


async def test_chat_send_is_rejected_before_the_model_is_called(client, owner_engine, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_USER_PER_MINUTE", "0")
    get_settings.cache_clear()
    await commit_operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    created = await client.post("/api/v1/chat/sessions", json={}, headers=headers)
    blocked = await client.post(
        f"/api/v1/chat/sessions/{created.json()['id']}/messages",
        json={"text": "hello"},
        headers={**headers, **ORIGIN},
    )
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Too many requests"}
    assert blocked.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_nightly_purge_drops_expired_revocations_only(owner_engine):
    from src.core.revocation_purge import purge_expired_revocations

    async with owner_engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO revoked_tokens (jti, expires_at) VALUES "
                "('expired-jti', now() - interval '1 minute'), "
                "('fresh-jti', now() + interval '1 day')"
            )
        )
    await purge_expired_revocations()
    async with owner_engine.connect() as connection:
        remaining = set((await connection.execute(text("SELECT jti FROM revoked_tokens"))).scalars().all())
    assert "expired-jti" not in remaining
    assert "fresh-jti" in remaining
