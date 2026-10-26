#!/usr/bin/env python3
# ******************************************************************************
# * @file    auth_service.py
# * @author  Simeon Marlokov
# * @brief   Authentication logic: credential check, token issue/resolve
# * @date    25.10.2026
# ******************************************************************************
from datetime import UTC, datetime

import bcrypt

from src.core.exceptions import UnauthorizedError
from src.core.revocation import cached_revoked, remember_revoked
from src.core.security import TokenClaims, create_access_token, decode_access_token, verify_password
from src.db.session import bind_organization
from src.models.audit_event import AuditEvent
from src.models.organization import Organization
from src.models.user import User
from src.repositories.organization_repository import OrganizationRepository
from src.repositories.revoked_token_repository import RevokedTokenRepository
from src.repositories.user_repository import UserRepository

# Cost 12 matches password hashes so a missing account takes as long as a wrong password.
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt(rounds=12)).decode()


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        organizations: OrganizationRepository,
        revoked: RevokedTokenRepository | None = None,
    ):
        self.users = users
        self.organizations = organizations
        self.revoked = revoked or RevokedTokenRepository(users.session)

    async def login(self, email: str, password: str) -> tuple[str, int]:
        user = await self.users.find_for_login(email)
        password_hash = user.password_hash if user is not None and user.is_active else DUMMY_PASSWORD_HASH
        password_ok = verify_password(password, password_hash)
        if user is None or not user.is_active or not password_ok:
            raise UnauthorizedError("Invalid email or password")
        await bind_organization(self.users.session, user.organization_id)
        self.users.session.add(
            AuditEvent(
                organization_id=user.organization_id,
                actor_type="user",
                actor_id=user.id,
                event="login",
                payload={},
            )
        )
        await self.users.session.commit()
        return create_access_token(user)

    async def logout(self, user: User, claims: TokenClaims) -> None:
        await self.revoked.purge_expired()
        await self.revoked.revoke(claims.jti, datetime.fromtimestamp(claims.exp, UTC))
        await bind_organization(self.users.session, user.organization_id)
        self.users.session.add(
            AuditEvent(
                organization_id=user.organization_id,
                actor_type="user",
                actor_id=user.id,
                event="logout",
                payload={},
            )
        )
        await self.users.session.commit()
        remember_revoked(claims.jti, True)

    async def get_user_from_token(self, token: str) -> tuple[User, TokenClaims]:
        claims = decode_access_token(token)
        user = await self.users.find_for_auth(claims.sub) if claims is not None else None
        if claims is None or user is None or not user.is_active:
            raise UnauthorizedError("Invalid or expired token")
        revoked = await self._jti_revoked(claims.jti)
        if revoked:
            raise UnauthorizedError("Invalid or expired token")
        return user, claims

    async def _jti_revoked(self, jti: str) -> bool:
        cached = cached_revoked(jti)
        if cached is not None:
            return cached
        revoked = await self.revoked.is_revoked(jti)
        remember_revoked(jti, revoked)
        return revoked

    async def get_profile(self, user: User) -> tuple[User, Organization]:
        organization = await self.organizations.get_by_id(user.organization_id)
        if organization is None:
            raise UnauthorizedError("Invalid or expired token")
        return user, organization
