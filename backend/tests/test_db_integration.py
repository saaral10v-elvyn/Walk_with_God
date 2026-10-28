"""Read-only integration tests.

Skipped by default so the suite never touches a real database by accident.
Run explicitly with:  $env:RUN_DB_TESTS="1"; uv run pytest tests/test_db_integration.py
"""

import os

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import create_engine_from_settings

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skipif(
        os.getenv("RUN_DB_TESTS") != "1",
        reason="Set RUN_DB_TESTS=1 to run database integration tests.",
    ),
]


async def test_database_is_reachable_and_migrated() -> None:
    engine = create_engine_from_settings(get_settings())
    try:
        async with engine.connect() as connection:
            value = (await connection.execute(text("SELECT 1"))).scalar_one()
            revision = (
                await connection.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one()
    finally:
        await engine.dispose()

    assert value == 1
    assert revision
