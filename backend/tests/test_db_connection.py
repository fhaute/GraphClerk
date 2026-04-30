from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy import text


def test_database_connection() -> None:
    """Verify we can make a real database connection when configured.

    This is an integration test. It is skipped unless explicitly enabled.
    """

    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set; skipping database connectivity test.")

    # Do not depend on full app Settings for this test; only DATABASE_URL is required.
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1")).scalar_one()

    assert res == 1

