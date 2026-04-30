from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_neighborhood_depth_1_and_depth_2(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        c = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "C"})).json()["id"]

        ab = (
            await client.post(
                "/graph/edges",
                json={"from_node_id": a, "to_node_id": b, "relation_type": "supports"},
            )
        ).json()["id"]
        bc = (
            await client.post(
                "/graph/edges",
                json={"from_node_id": b, "to_node_id": c, "relation_type": "supports"},
            )
        ).json()["id"]

        # Attach minimal evidence refs (support_type + confidence).
        art = (
            await client.post(
                "/artifacts",
                json={"filename": "x.txt", "artifact_type": "text", "text": "Hello"},
            )
        ).json()
        ev_list = (await client.get(f"/artifacts/{art['artifact_id']}/evidence")).json()["items"]
        eu = ev_list[0]["id"]

        await client.post(
            f"/graph/nodes/{a}/evidence",
            json={"evidence_unit_id": eu, "support_type": "quote", "confidence": 0.9},
        )
        await client.post(
            f"/graph/edges/{ab}/evidence",
            json={"evidence_unit_id": eu, "support_type": "quote", "confidence": 0.8},
        )

        d1 = await client.get(f"/graph/nodes/{a}/neighborhood", params={"depth": 1})
        assert d1.status_code == 200
        body1 = d1.json()
        assert body1["start_node_id"] == a
        assert body1["depth"] == 1
        assert body1["truncated"] is False
        assert {n["id"] for n in body1["nodes"]} == {a, b}
        assert {e["id"] for e in body1["edges"]} == {ab}
        assert any(x["node_id"] == a for x in body1["node_evidence"])
        assert any(x["edge_id"] == ab for x in body1["edge_evidence"])

        d2 = await client.get(f"/graph/nodes/{a}/neighborhood", params={"depth": 2})
        assert d2.status_code == 200
        body2 = d2.json()
        assert {n["id"] for n in body2["nodes"]} == {a, b, c}
        assert {e["id"] for e in body2["edges"]} == {ab, bc}


@pytest.mark.asyncio
async def test_neighborhood_max_nodes_prevents_edge_leak(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        c = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "C"})).json()["id"]

        ab = (
            await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "supports"})
        ).json()["id"]
        bc = (
            await client.post("/graph/edges", json={"from_node_id": b, "to_node_id": c, "relation_type": "supports"})
        ).json()["id"]

        res = await client.get(f"/graph/nodes/{a}/neighborhood", params={"depth": 2, "max_nodes": 2})
        assert res.status_code == 200
        body = res.json()
        assert body["truncated"] is True
        assert "max_nodes_reached" in body["truncation_reasons"]
        assert {n["id"] for n in body["nodes"]} == {a, b}
        assert {e["id"] for e in body["edges"]} == {ab}
        assert bc not in {e["id"] for e in body["edges"]}


@pytest.mark.asyncio
async def test_neighborhood_max_edges_sets_truncated(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        c = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "C"})).json()["id"]

        await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "supports"})
        await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": c, "relation_type": "supports"})

        res = await client.get(f"/graph/nodes/{a}/neighborhood", params={"depth": 1, "max_edges": 1})
        assert res.status_code == 200
        body = res.json()
        assert body["truncated"] is True
        assert "max_edges_reached" in body["truncation_reasons"]
        assert len(body["edges"]) == 1


@pytest.mark.asyncio
async def test_neighborhood_relation_filter_and_invalid_relation_type(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]

        supports = (
            await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "supports"})
        ).json()["id"]
        await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "explains"})

        res = await client.get(
            f"/graph/nodes/{a}/neighborhood",
            params=[("relation_types", "supports"), ("depth", 1)],
        )
        assert res.status_code == 200
        body = res.json()
        assert {e["id"] for e in body["edges"]} == {supports}

        bad = await client.get(
            f"/graph/nodes/{a}/neighborhood",
            params=[("relation_types", "not-a-real-type"), ("depth", 1)],
        )
        assert bad.status_code == 422


@pytest.mark.asyncio
async def test_neighborhood_invalid_node_id_returns_404(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/graph/nodes/not-a-uuid/neighborhood")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_neighborhood_depth_gt_3_rejected(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        res = await client.get(f"/graph/nodes/{a}/neighborhood", params={"depth": 4})
        assert res.status_code == 422

