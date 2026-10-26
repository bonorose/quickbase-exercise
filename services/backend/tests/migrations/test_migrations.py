import os
import subprocess
import sys

import pytest
from sqlalchemy import text
from tests.conftest import BACKEND_ROOT

from src.core.config import get_settings

pytestmark = pytest.mark.api


async def test_upgrade_downgrade_upgrade_and_check(owner_engine):
    async with owner_engine.connect() as connection:
        autocommit = await connection.execution_options(isolation_level="AUTOCOMMIT")
        await autocommit.execute(text("DROP DATABASE IF EXISTS qai_migtest"))
        await autocommit.execute(text("CREATE DATABASE qai_migtest"))
    url = get_settings().migration_database_url.set(database="qai_migtest").render_as_string(hide_password=False)
    env = os.environ.copy()
    env["ALEMBIC_DATABASE_URL"] = url
    # Roles are cluster-wide. Keep this round-trip off the role the session database is using.
    env["POSTGRES_APP_USER"] = "qai_app_migtest"
    try:
        for command in (["upgrade", "head"], ["downgrade", "base"], ["upgrade", "head"], ["check"]):
            subprocess.run(
                [sys.executable, "-m", "alembic", *command],
                cwd=BACKEND_ROOT,
                check=True,
                env=env,
            )
    finally:
        async with owner_engine.connect() as connection:
            autocommit = await connection.execution_options(isolation_level="AUTOCOMMIT")
            await autocommit.execute(text("DROP DATABASE IF EXISTS qai_migtest"))
