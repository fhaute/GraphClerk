from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.main import create_app


async def _create_text_artifact_and_get_evidence_unit_id(client: httpx.AsyncClient) -> str:
    created = await client.post(
        "/artifacts",
        json={"filename": "a.txt", "artifact_type": "text", "text": "Hello\n\nWorld\n"},
    )
    artifact_id = created.json()["artifact_id"]
    evs = await client.get(f"/artifacts/{artifact_id}/evidence")
    return evs.json()["items"][0]["id"]


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_node(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        node_id = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        ev_id = await _create_text_artifact_and_get_evidence_unit_id(client)

        res = await client.post(
            f"/graph/nodes/{node_id}/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports", "confidence": 0.8},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["graph_node_id"] == node_id
        assert body["evidence_unit_id"] == ev_id
        assert body["support_type"] == "supports"
        assert body["confidence"] == 0.8


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_node_invalid_node_id_404(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ev_id = await _create_text_artifact_and_get_evidence_unit_id(client)
        res = await client.post(
            "/graph/nodes/00000000-0000-0000-0000-000000000000/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_node_invalid_evidence_unit_id_404(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        node_id = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        res = await client.post(
            f"/graph/nodes/{node_id}/evidence",
            json={
                "evidence_unit_id": "00000000-0000-0000-0000-000000000000",
                "support_type": "supports",
            },
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_node_duplicate_conflict_409(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        node_id = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        ev_id = await _create_text_artifact_and_get_evidence_unit_id(client)

        first = await client.post(
            f"/graph/nodes/{node_id}/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports"},
        )
        assert first.status_code == 200

        second = await client.post(
            f"/graph/nodes/{node_id}/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports"},
        )
        assert second.status_code == 409
        assert second.json()["detail"] == "graph_node_evidence_link_already_exists"


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_edge(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        edge_id = (
            await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "related_to"})
        ).json()["id"]
        ev_id = await _create_text_artifact_and_get_evidence_unit_id(client)

        res = await client.post(
            f"/graph/edges/{edge_id}/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports", "confidence": 1.0},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["graph_edge_id"] == edge_id
        assert body["evidence_unit_id"] == ev_id
        assert body["support_type"] == "supports"
        assert body["confidence"] == 1.0


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_edge_invalid_edge_id_404(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        ev_id = await _create_text_artifact_and_get_evidence_unit_id(client)
        res = await client.post(
            "/graph/edges/00000000-0000-0000-0000-000000000000/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_edge_invalid_evidence_unit_id_404(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        edge_id = (
            await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "related_to"})
        ).json()["id"]
        res = await client.post(
            f"/graph/edges/{edge_id}/evidence",
            json={
                "evidence_unit_id": "00000000-0000-0000-0000-000000000000",
                "support_type": "supports",
            },
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_attach_evidence_to_graph_edge_duplicate_conflict_409(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        a = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "A"})).json()["id"]
        b = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "B"})).json()["id"]
        edge_id = (
            await client.post("/graph/edges", json={"from_node_id": a, "to_node_id": b, "relation_type": "related_to"})
        ).json()["id"]
        ev_id = await _create_text_artifact_and_get_evidence_unit_id(client)

        first = await client.post(
            f"/graph/edges/{edge_id}/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports"},
        )
        assert first.status_code == 200

        second = await client.post(
            f"/graph/edges/{edge_id}/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports"},
        )
        assert second.status_code == 409
        assert second.json()["detail"] == "graph_edge_evidence_link_already_exists"


@pytest.mark.asyncio
async def test_invalid_confidence_rejected(db_ready: None) -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        node_id = (await client.post("/graph/nodes", json={"node_type": "concept", "label": "N"})).json()["id"]
        ev_id = await _create_text_artifact_and_get_evidence_unit_id(client)

        res = await client.post(
            f"/graph/nodes/{node_id}/evidence",
            json={"evidence_unit_id": ev_id, "support_type": "supports", "confidence": 1.5},
        )
        assert res.status_code == 422

