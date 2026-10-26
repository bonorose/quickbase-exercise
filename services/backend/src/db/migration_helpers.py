#!/usr/bin/env python3
# ******************************************************************************
# * @file    migration_helpers.py
# * @author  Simeon Marlokov
# * @brief   Shared Alembic operations. Every organization-owned table calls
# *          enable_organization_rls before the migration that creates it ends.
# * @date    25.10.2026
# ******************************************************************************
from alembic import op


def enable_organization_rls(table: str, column: str = "organization_id") -> None:
    """Force row-level security. An unset app.organization_id matches nothing."""
    predicate = f"{column} = NULLIF(current_setting('app.organization_id', true), '')::bigint"
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {table}_organization_isolation ON {table} USING ({predicate}) WITH CHECK ({predicate})")


def disable_organization_rls(table: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {table}_organization_isolation ON {table}")
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
