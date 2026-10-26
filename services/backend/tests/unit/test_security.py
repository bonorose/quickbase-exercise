from datetime import UTC, datetime, timedelta

import jwt
import pytest

from src.core.config import get_settings
from src.core.security import create_access_token, decode_access_token, hash_password, verify_password
from src.models.user import User

pytestmark = pytest.mark.unit


def _user() -> User:
    return User(
        id=4,
        email="op1@excellence.qai.local",
        password_hash="x",
        name="Operator",
        organization_id=9,
        role="operator",
        is_active=True,
    )


def test_password_roundtrip():
    hashed = hash_password("correct horse")
    assert hashed != "correct horse"
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_claims_and_expiry():
    token, expires_in = create_access_token(_user())
    claims = decode_access_token(token)
    settings = get_settings()
    assert expires_in == settings.jwt_expire_minutes * 60
    assert claims is not None
    assert claims.sub == 4
    assert claims.organization_id == 9
    assert claims.role == "operator"
    assert claims.jti
    assert claims.exp > int(datetime.now(UTC).timestamp())


def test_rejects_expired_wrong_secret_and_legacy_tokens():
    settings = get_settings()
    user = _user()
    expired = jwt.encode(
        {
            "sub": "4",
            "organization_id": 9,
            "role": "operator",
            "jti": "abc",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    wrong_secret = jwt.encode(
        {
            "sub": "4",
            "organization_id": 9,
            "role": "operator",
            "jti": "abc",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "other-secret",
        algorithm=settings.jwt_algorithm,
    )
    legacy = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert decode_access_token(expired) is None
    assert decode_access_token(wrong_secret) is None
    assert decode_access_token(legacy) is None
    assert decode_access_token("not-a-token") is None


async def test_docs_are_public(app):
    import httpx

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/docs")
    assert response.status_code == 200
