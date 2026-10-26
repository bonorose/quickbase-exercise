"""Drop the placeholder items slice.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-25
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS items")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")


def downgrade() -> None:
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
