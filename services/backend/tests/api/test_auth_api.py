from datetime import UTC, datetime, timedelta

import jwt
import pytest
from tests.factories import commit_operator
from tests.helpers.auth import auth_header

from src.core.config import get_settings
from src.core.security import decode_access_token

pytestmark = pytest.mark.api


async def test_login_issues_organization_claims_and_me_shape(client, owner_engine):
    await commit_operator(owner_engine, role="team_lead", name="Excellence Lead", email="lead@excellence.qai.local")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "lead@excellence.qai.local", "password": "password"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["expires_in"] == get_settings().jwt_expire_minutes * 60
    claims = decode_access_token(body["access_token"])
    assert claims is not None
    assert claims.role == "team_lead"
    assert claims.jti
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["name"] == "Excellence Lead"
    assert me.json()["role"] == "team_lead"
    assert me.json()["organization"] == {"id": claims.organization_id, "name": "Excellence"}
    assert set(me.json()) == {"id", "name", "email", "role", "organization"}


async def test_legacy_token_and_organization_mismatch_are_401(client, owner_engine):
    organization_id, user_id = await commit_operator(owner_engine)
    settings = get_settings()
    legacy = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    mismatch = jwt.encode(
        {
            "sub": str(user_id),
            "organization_id": organization_id + 50,
            "role": "operator",
            "jti": "mismatch",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {legacy}"})).status_code == 401
    assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {mismatch}"})).status_code == 401
    headers = await auth_header(client, "op1@excellence.qai.local")
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 200


async def test_login_is_case_insensitive(client, owner_engine):
    await commit_operator(owner_engine, email="Op1@Excellence.qai.local")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "op1@excellence.qai.local", "password": "password"},
    )
    assert response.status_code == 200
