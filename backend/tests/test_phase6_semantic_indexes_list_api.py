from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_list_semantic_indexes_empty(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/semantic-indexes")
        assert res.status_code == 200
        body = res.json()
        assert body["items"] == []
        assert body["count"] == 0
        assert body["limit"] == 100
        assert body["offset"] == 0


@pytest.mark.asyncio
async def test_list_semantic_indexes_entry_node_ids_from_join_table(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        created = await client.post(
            "/semantic-indexes",
            json={"meaning": "joined", "entry_node_ids": [n]},
        )
        assert created.status_code == 200
        sid = created.json()["id"]

        listed = await client.get("/semantic-indexes")
        assert listed.status_code == 200
        body = listed.json()
        assert body["count"] == 1
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["id"] == sid
        assert item["entry_node_ids"] == [n]
        assert item["vector_status"] == "pending"

        got_one = await client.get(f"/semantic-indexes/{sid}")
        assert got_one.json()["entry_node_ids"] == item["entry_node_ids"]


@pytest.mark.asyncio
async def test_list_semantic_indexes_pagination(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        n = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        for i in range(3):
            r = await client.post(
                "/semantic-indexes",
                json={"meaning": f"m{i}", "entry_node_ids": [n]},
            )
            assert r.status_code == 200

        page0 = await client.get("/semantic-indexes", params={"limit": 1, "offset": 0})
        assert page0.status_code == 200
        b0 = page0.json()
        assert b0["count"] == 3
        assert len(b0["items"]) == 1
        assert b0["limit"] == 1
        assert b0["offset"] == 0
        assert b0["items"][0]["meaning"] == "m2"

        page1 = await client.get("/semantic-indexes", params={"limit": 1, "offset": 1})
        assert page1.json()["items"][0]["meaning"] == "m1"

        page2 = await client.get("/semantic-indexes", params={"limit": 10, "offset": 0})
        assert len(page2.json()["items"]) == 3


@pytest.mark.asyncio
async def test_list_semantic_indexes_validation_limit_zero() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/semantic-indexes", params={"limit": 0})
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_list_semantic_indexes_validation_limit_over_max() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/semantic-indexes", params={"limit": 201})
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_list_semantic_indexes_validation_negative_offset() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/semantic-indexes", params={"offset": -1})
        assert res.status_code == 422
