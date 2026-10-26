"""Append-only audit events.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.core.config import get_settings
from src.db.migration_helpers import disable_organization_rls, enable_organization_rls

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("organization_id", sa.BigInteger, nullable=False),
        sa.Column("actor_type", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.BigInteger, nullable=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("session_id", UUID(as_uuid=True), nullable=True),
        sa.Column("ticket_id", sa.BigInteger, nullable=True),
        sa.Column("pending_revision_id", UUID(as_uuid=True), nullable=True),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("date_created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("actor_type IN ('user', 'agent', 'system')", name="audit_events_actor_type_check"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_audit_events_organization_id"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_audit_events_actor_id"),
        sa.ForeignKeyConstraint(
            ["pending_revision_id"], ["pending_revisions.id"], name="fk_audit_events_pending_revision_id"
        ),
    )
    enable_organization_rls("audit_events")
    user = get_settings().postgres_app_user.replace('"', "")
    op.execute(f"GRANT SELECT, INSERT ON audit_events TO {user}")
    op.execute(f"REVOKE UPDATE, DELETE ON audit_events FROM {user}")
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {user}")


def downgrade() -> None:
    disable_organization_rls("audit_events")
    op.drop_table("audit_events")
