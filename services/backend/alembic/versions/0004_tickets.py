"""Tickets, revisions, and discussions.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.db.migration_helpers import disable_organization_rls, enable_organization_rls
from src.core.config import get_settings

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE FUNCTION set_date_updated()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.date_updated = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.create_table(
        "tickets",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("organization_id", sa.BigInteger, nullable=False),
        sa.Column("status", sa.SmallInteger, nullable=False),
        sa.Column("priority", sa.SmallInteger, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("contents", sa.String(2000), nullable=False),
        sa.Column("submitted_by", sa.String(255), nullable=False),
        sa.Column("updated_by", sa.BigInteger, nullable=True),
        sa.Column("date_created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("date_updated", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("date_deleted", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN (1, 2, 3)", name="tickets_status_check"),
        sa.CheckConstraint("priority IN (1, 2, 3, 4, 5)", name="tickets_priority_check"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_tickets_organization_id"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], name="fk_tickets_updated_by"),
        sa.UniqueConstraint("organization_id", "id", name="tickets_organization_id_id_key"),
    )
    op.create_index("tickets_organization_status_idx", "tickets", ["organization_id", "status"])
    op.create_index(
        "tickets_organization_date_updated_idx",
        "tickets",
        ["organization_id", sa.text("date_updated DESC")],
    )
    op.execute(
        "CREATE INDEX tickets_search_trgm ON tickets USING gin "
        "((title || ' ' || description || ' ' || contents) gin_trgm_ops)"
    )
    op.execute(
        """
        CREATE TRIGGER tickets_set_date_updated
            BEFORE UPDATE ON tickets
            FOR EACH ROW EXECUTE FUNCTION set_date_updated()
        """
    )
    op.create_table(
        "revisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", sa.BigInteger, nullable=False),
        sa.Column("organization_id", sa.BigInteger, nullable=False),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("initial_contents", JSONB, nullable=False),
        sa.Column("changed_contents", JSONB, nullable=False),
        sa.Column("date_created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_revisions_organization_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_revisions_user_id"),
        sa.ForeignKeyConstraint(
            ["organization_id", "ticket_id"],
            ["tickets.organization_id", "tickets.id"],
            name="fk_revisions_ticket_organization",
        ),
    )
    op.create_table(
        "discussions",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("ticket_id", sa.BigInteger, nullable=False),
        sa.Column("organization_id", sa.BigInteger, nullable=False),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("contents", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_discussions_organization_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_discussions_user_id"),
        sa.ForeignKeyConstraint(
            ["organization_id", "ticket_id"],
            ["tickets.organization_id", "tickets.id"],
            name="fk_discussions_ticket_organization",
        ),
    )
    enable_organization_rls("tickets")
    enable_organization_rls("revisions")
    enable_organization_rls("discussions")
    user = get_settings().postgres_app_user.replace('"', "")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON tickets, revisions, discussions TO {user}")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO " + user)


def downgrade() -> None:
    disable_organization_rls("discussions")
    disable_organization_rls("revisions")
    disable_organization_rls("tickets")
    op.drop_table("discussions")
    op.drop_table("revisions")
    op.execute("DROP TABLE tickets")
    op.execute("DROP FUNCTION IF EXISTS set_date_updated()")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
