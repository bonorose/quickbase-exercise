"""Chat sessions and messages.

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.core.config import get_settings
from src.db.migration_helpers import disable_organization_rls, enable_organization_rls

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.BigInteger, nullable=False),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("date_created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_chat_sessions_organization_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_chat_sessions_user_id"),
        sa.UniqueConstraint("organization_id", "id", name="chat_sessions_organization_id_id_key"),
    )
    op.create_index(
        "chat_sessions_owner_activity_idx",
        "chat_sessions",
        ["organization_id", "user_id", sa.text("last_activity_at DESC")],
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.BigInteger, nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("date_created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant', 'tool')", name="chat_messages_role_check"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_chat_messages_organization_id"),
        sa.ForeignKeyConstraint(
            ["organization_id", "session_id"],
            ["chat_sessions.organization_id", "chat_sessions.id"],
            name="fk_chat_messages_session_organization",
        ),
    )
    enable_organization_rls("chat_sessions")
    enable_organization_rls("chat_messages")
    user = get_settings().postgres_app_user.replace('"', "")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON chat_sessions, chat_messages TO {user}")
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {user}")


def downgrade() -> None:
    disable_organization_rls("chat_messages")
    disable_organization_rls("chat_sessions")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
