from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_create_graph_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})
        assert res.status_code == 200
        body = res.json()
        assert body["id"]
        assert body["node_type"] == "concept"
        assert body["label"] == "N"


@pytest.mark.asyncio
async def test_get_graph_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})
        node_id = created.json()["id"]

        got = await client.get(f"/graph/nodes/{node_id}")
        assert got.status_code == 200
        assert got.json()["id"] == node_id


@pytest.mark.asyncio
async def test_list_graph_nodes(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})
        await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})
        res = await client.get("/graph/nodes")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 2


@pytest.mark.asyncio
async def test_create_graph_edge(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]

        res = await client.post(
            "/graph/edges",
            json={
                "from_node_id": a,
                "to_node_id": b,
                "relation_type": "related_to",
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["id"]
        assert body["from_node_id"] == a
        assert body["to_node_id"] == b
        assert body["relation_type"] == "related_to"


@pytest.mark.asyncio
async def test_get_graph_edge(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        edge_id = (
            await client.post(
                "/graph/edges",
                json={"from_node_id": a, "to_node_id": b, "relation_type": "related_to"},
            )
        ).json()["id"]

        got = await client.get(f"/graph/edges/{edge_id}")
        assert got.status_code == 200
        assert got.json()["id"] == edge_id


@pytest.mark.asyncio
async def test_list_graph_edges(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "related_to"})
        res = await client.get("/graph/edges")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1


@pytest.mark.asyncio
async def test_invalid_relation_type_fails(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        res = await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "bogus"})
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_graph_edge_requires_valid_from_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        res = await client.post(
            "/graph/edges",
            json={
                "from_node_id": "00000000-0000-0000-0000-000000000000",
                "to_node_id": b,
                "relation_type": "related_to",
            },
        )
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_graph_edge_requires_valid_to_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        res = await client.post(
            "/graph/edges",
            json={
                "from_node_id": a,
                "to_node_id": "00000000-0000-0000-0000-000000000000",
                "relation_type": "related_to",
            },
        )
        assert res.status_code == 400

