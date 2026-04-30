from __future__ import annotations

import os

import pytest
import httpx
from httpx import ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_get_artifact_endpoint(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={"filename": "a.txt", "artifact_type": "text", "text": "Hello\n\nWorld\n"},
        )
        assert res.status_code == 200
        artifact_id = res.json()["artifact_id"]

        got = await client.get(f"/artifacts/{artifact_id}")
        assert got.status_code == 200
        body = got.json()
        assert body["id"] == artifact_id
        assert body["checksum"]


@pytest.mark.asyncio
async def test_list_artifacts_endpoint(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/artifacts",
            json={"filename": "a.txt", "artifact_type": "text", "text": "Hello"},
        )
        res = await client.get("/artifacts")
        assert res.status_code == 200
        assert "items" in res.json()


@pytest.mark.asyncio
async def test_list_artifact_evidence_endpoint(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={"filename": "a.txt", "artifact_type": "text", "text": "A\n\nB\n"},
        )
        artifact_id = res.json()["artifact_id"]

        evs = await client.get(f"/artifacts/{artifact_id}/evidence")
        assert evs.status_code == 200
        items = evs.json()["items"]
        assert len(items) == 2
        assert all(it["artifact_id"] == artifact_id for it in items)


@pytest.mark.asyncio
async def test_get_evidence_unit_endpoint(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={"filename": "a.txt", "artifact_type": "text", "text": "A\n\nB\n"},
        )
        artifact_id = res.json()["artifact_id"]
        evs = await client.get(f"/artifacts/{artifact_id}/evidence")
        evidence_unit_id = evs.json()["items"][0]["id"]

        got = await client.get(f"/evidence-units/{evidence_unit_id}")
        assert got.status_code == 200
        assert got.json()["id"] == evidence_unit_id


@pytest.mark.asyncio
async def test_unsupported_file_type_fails_clearly(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("x.pdf", b"%PDF-1.4", "application/pdf")}
        res = await client.post("/artifacts", files=files)
        assert res.status_code == 400

