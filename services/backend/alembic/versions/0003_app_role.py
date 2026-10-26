"""Application role, auth functions, and RLS on identity tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-25
"""

from alembic import op

from src.db.migration_helpers import disable_organization_rls, enable_organization_rls
from src.core.config import get_settings

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    password = get_settings().postgres_app_password.replace("'", "''")
    user = get_settings().postgres_app_user.replace('"', "")
    # Roles are cluster-wide. A second database on the same server must not fail the upgrade.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{user}') THEN
                CREATE ROLE {user} LOGIN PASSWORD '{password}'
                    NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
            END IF;
        END
        $$
        """
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {user}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {user}")
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {user}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {user}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {user}")
    op.execute(
        """
        CREATE FUNCTION auth_find_user(p_email text)
        RETURNS SETOF users
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public
        AS $$
            SELECT * FROM users WHERE lower(email) = lower(p_email)
        $$
        """
    )
    op.execute(
        """
        CREATE FUNCTION auth_get_user(p_id bigint)
        RETURNS SETOF users
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public
        AS $$
            SELECT * FROM users WHERE id = p_id
        $$
        """
    )
    op.execute(f"GRANT EXECUTE ON FUNCTION auth_find_user(text) TO {user}")
    op.execute(f"GRANT EXECUTE ON FUNCTION auth_get_user(bigint) TO {user}")
    enable_organization_rls("users")
    enable_organization_rls("organizations", column="id")


def downgrade() -> None:
    user = get_settings().postgres_app_user.replace('"', "")
    disable_organization_rls("organizations")
    disable_organization_rls("users")
    op.execute("DROP FUNCTION IF EXISTS auth_get_user(bigint)")
    op.execute("DROP FUNCTION IF EXISTS auth_find_user(text)")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM {user}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM {user}")
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {user}")
    op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {user}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {user}")
    op.execute(f"DROP ROLE IF EXISTS {user}")
