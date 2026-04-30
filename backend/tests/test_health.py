from __future__ import annotations

import pytest
import httpx
from httpx import ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """GET /health returns a minimal ok status in Phase 1."""

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")

    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

