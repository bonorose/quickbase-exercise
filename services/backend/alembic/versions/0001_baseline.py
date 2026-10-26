"""Baseline schema: users, items, set_updated_at.

Revision ID: 0001
Revises:
Create Date: 2026-10-25
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TABLE users (
            id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            email         VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            full_name     VARCHAR(255) NOT NULL,
            is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE items (
            id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name        VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TRIGGER items_set_updated_at
            BEFORE UPDATE ON items
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS items")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
