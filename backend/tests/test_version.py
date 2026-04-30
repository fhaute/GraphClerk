from __future__ import annotations

import pytest
import httpx
from httpx import ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_version_endpoint() -> None:
    """GET /version returns GraphClerk and Phase 2 metadata."""

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/version")

    assert res.status_code == 200
    assert res.json() == {"name": "GraphClerk", "version": "0.1.0", "phase": "phase_2_text_first_ingestion"}

