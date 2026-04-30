from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_create_semantic_index(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        res = await client.post(
            "/semantic-indexes",
            json={"meaning": "m", "entry_node_ids": [n]},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["id"]
        assert body["meaning"] == "m"
        assert body["entry_node_ids"] == [n]
        assert body["vector_status"] == "pending"


@pytest.mark.asyncio
async def test_create_semantic_index_requires_entry_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/semantic-indexes", json={"meaning": "m", "entry_node_ids": []})
        assert res.status_code in (400, 422)


@pytest.mark.asyncio
async def test_create_semantic_index_rejects_missing_entry_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/semantic-indexes",
            json={"meaning": "m", "entry_node_ids": ["00000000-0000-0000-0000-000000000000"]},
        )
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_create_semantic_index_rejects_duplicate_entry_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        res = await client.post(
            "/semantic-indexes",
            json={"meaning": "m", "entry_node_ids": [n, n]},
        )
        assert res.status_code == 400
        assert res.json()["detail"] == "duplicate_entry_node_id"


@pytest.mark.asyncio
async def test_get_semantic_index(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        created = await client.post("/semantic-indexes", json={"meaning": "m", "entry_node_ids": [n]})
        semantic_index_id = created.json()["id"]

        got = await client.get(f"/semantic-indexes/{semantic_index_id}")
        assert got.status_code == 200
        body = got.json()
        assert body["id"] == semantic_index_id
        assert body["entry_node_ids"] == [n]


@pytest.mark.asyncio
async def test_resolve_semantic_index_entry_points(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        created = await client.post("/semantic-indexes", json={"meaning": "m", "entry_node_ids": [n]})
        semantic_index_id = created.json()["id"]

        res = await client.get(f"/semantic-indexes/{semantic_index_id}/entry-points")
        assert res.status_code == 200
        assert res.json()["entry_node_ids"] == [n]


@pytest.mark.asyncio
async def test_create_semantic_index_rejects_invalid_uuid_entry_node_id(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/semantic-indexes", json={"meaning": "m", "entry_node_ids": ["not-a-uuid"]})
        assert res.status_code == 400

