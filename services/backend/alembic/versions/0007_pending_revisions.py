"""Pending revisions and system chat notes.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.core.config import get_settings
from src.db.migration_helpers import disable_organization_rls, enable_organization_rls

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_revisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", sa.BigInteger, nullable=False),
        sa.Column("organization_id", sa.BigInteger, nullable=False),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("previous_revision_id", UUID(as_uuid=True), nullable=True),
        sa.Column("changed_contents", JSONB, nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("tainted", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.BigInteger, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("session_id", UUID(as_uuid=True), nullable=True),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("date_created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("date_updated", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("action IN ('update', 'delete')", name="pending_revisions_action_check"),
        sa.CheckConstraint(
            "status IN ('open', 'executed', 'rejected', 'expired')",
            name="pending_revisions_status_check",
        ),
        sa.CheckConstraint("origin IN ('human', 'agent')", name="pending_revisions_origin_check"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_pending_revisions_organization_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_pending_revisions_user_id"),
        sa.ForeignKeyConstraint(
            ["previous_revision_id"], ["revisions.id"], name="fk_pending_revisions_previous_revision"
        ),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"], name="fk_pending_revisions_decided_by"),
        sa.ForeignKeyConstraint(
            ["organization_id", "ticket_id"],
            ["tickets.organization_id", "tickets.id"],
            name="fk_pending_revisions_ticket_organization",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "session_id"],
            ["chat_sessions.organization_id", "chat_sessions.id"],
            name="fk_pending_revisions_session",
        ),
        sa.UniqueConstraint("organization_id", "id", name="pending_revisions_organization_id_id_key"),
    )
    op.create_index(
        "pending_revisions_one_open_idx",
        "pending_revisions",
        ["ticket_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    enable_organization_rls("pending_revisions")
    user = get_settings().postgres_app_user.replace('"', "")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON pending_revisions TO {user}")
    op.drop_constraint("chat_messages_role_check", "chat_messages", type_="check")
    op.create_check_constraint(
        "chat_messages_role_check",
        "chat_messages",
        "role IN ('user', 'assistant', 'tool', 'system')",
    )


def downgrade() -> None:
    op.drop_constraint("chat_messages_role_check", "chat_messages", type_="check")
    op.create_check_constraint(
        "chat_messages_role_check",
        "chat_messages",
        "role IN ('user', 'assistant', 'tool')",
    )
    disable_organization_rls("pending_revisions")
    op.drop_index("pending_revisions_one_open_idx", table_name="pending_revisions")
    op.drop_table("pending_revisions")
