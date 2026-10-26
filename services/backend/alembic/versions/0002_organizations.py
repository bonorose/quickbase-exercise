"""Organizations, user membership, case-insensitive email.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-25
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.BigInteger, sa.Identity(always=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("users", sa.Column("organization_id", sa.BigInteger(), nullable=True))
    # Backfill only when a volume already has users. A fresh database stays empty.
    op.execute(
        """
        INSERT INTO organizations (name)
        SELECT 'Excellence'
        WHERE EXISTS (SELECT 1 FROM users)
          AND NOT EXISTS (SELECT 1 FROM organizations WHERE name = 'Excellence')
        """
    )
    op.execute(
        "UPDATE users SET organization_id = (SELECT id FROM organizations WHERE name = 'Excellence') "
        "WHERE organization_id IS NULL"
    )
    op.alter_column("users", "organization_id", nullable=False)
    op.create_foreign_key("fk_users_organization_id", "users", "organizations", ["organization_id"], ["id"])
    op.add_column("users", sa.Column("role", sa.String(32), nullable=True))
    op.execute("UPDATE users SET role = 'operator' WHERE role IS NULL")
    op.alter_column("users", "role", nullable=False)
    op.create_check_constraint("users_role_check", "users", "role IN ('operator', 'team_lead')")
    op.alter_column("users", "full_name", new_column_name="name")
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_index("users_email_lower_key", "users", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index("users_email_lower_key", table_name="users")
    op.create_index("users_email_key", "users", ["email"], unique=True)
    op.alter_column("users", "name", new_column_name="full_name")
    op.drop_constraint("users_role_check", "users", type_="check")
    op.drop_column("users", "role")
    op.drop_constraint("fk_users_organization_id", "users", type_="foreignkey")
    op.drop_column("users", "organization_id")
    op.drop_table("organizations")
