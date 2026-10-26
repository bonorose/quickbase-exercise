"""Global token revocation list.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-26
"""

import sqlalchemy as sa
from alembic import op

from src.core.config import get_settings

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    user = get_settings().postgres_app_user.replace('"', "")
    op.execute(f"GRANT SELECT, INSERT, DELETE ON revoked_tokens TO {user}")


def downgrade() -> None:
    op.drop_table("revoked_tokens")
