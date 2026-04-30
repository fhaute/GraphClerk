from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from app.models.enums import GraphRelationType
from app.models.graph_edge import GraphEdge
from app.models.enums import GraphNodeType
from app.models.graph_node import GraphNode
from app.services.errors import GraphNodeNotFoundError
from app.services.graph_traversal_service import GraphTraversalService


@dataclass(frozen=True)
class _NodeEv:
    graph_node_id: uuid.UUID
    evidence_unit_id: uuid.UUID
    support_type: str
    confidence: float | None
    created_at: int = 0
    id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class _EdgeEv:
    graph_edge_id: uuid.UUID
    evidence_unit_id: uuid.UUID
    support_type: str
    confidence: float | None
    created_at: int = 0
    id: uuid.UUID = uuid.uuid4()


class _StubNodeRepo:
    def __init__(self, nodes: dict[uuid.UUID, GraphNode]) -> None:
        self._nodes = nodes

    def get(self, node_id: uuid.UUID):
        return self._nodes.get(node_id)

    def list_by_ids(self, node_ids: list[uuid.UUID]):
        return [self._nodes[n] for n in node_ids if n in self._nodes]


class _StubEdgeRepo:
    def __init__(self, edges: list[GraphEdge]) -> None:
        self._edges = edges

    def list_incident_edges(self, *, node_ids: list[uuid.UUID], relation_types=None, limit=5000):
        _ = limit
        out = [e for e in self._edges if (e.from_node_id in node_ids or e.to_node_id in node_ids)]
        if relation_types is not None:
            out = [e for e in out if str(e.relation_type) in set(relation_types)]
        return out


class _StubNodeEvRepo:
    def __init__(self, evs: list[_NodeEv]) -> None:
        self._evs = evs

    def list_by_graph_nodes(self, graph_node_ids: list[uuid.UUID], limit: int = 5000):
        _ = limit
        s = set(graph_node_ids)
        return [e for e in self._evs if e.graph_node_id in s]


class _StubEdgeEvRepo:
    def __init__(self, evs: list[_EdgeEv]) -> None:
        self._evs = evs

    def list_by_graph_edges(self, graph_edge_ids: list[uuid.UUID], limit: int = 5000):
        _ = limit
        s = set(graph_edge_ids)
        return [e for e in self._evs if e.graph_edge_id in s]


def _mk_node(nid: uuid.UUID) -> GraphNode:
    return GraphNode(id=nid, node_type=GraphNodeType.concept, label="L", summary=None, metadata_json=None)  # type: ignore[call-arg]


def _mk_edge(eid: uuid.UUID, a: uuid.UUID, b: uuid.UUID, rt: GraphRelationType) -> GraphEdge:
    return GraphEdge(  # type: ignore[call-arg]
        id=eid,
        from_node_id=a,
        to_node_id=b,
        relation_type=rt,
        summary=None,
        confidence=None,
        metadata_json=None,
    )


def test_happy_path_depth_1() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    e1 = uuid.uuid4()
    nodes = {a: _mk_node(a), b: _mk_node(b)}
    edges = [_mk_edge(e1, a, b, GraphRelationType.supports)]

    svc = GraphTraversalService(
        session=None,  # not used with stub repos
        node_repo=_StubNodeRepo(nodes),
        edge_repo=_StubEdgeRepo(edges),
        node_ev_repo=_StubNodeEvRepo([]),
        edge_ev_repo=_StubEdgeEvRepo([]),
    )
    res = svc.neighborhood(start_node_id=a, depth=1, max_nodes=25, max_edges=50)
    assert {n.id for n in res.nodes} == {a, b}
    assert {e.id for e in res.edges} == {e1}
    assert not res.truncated


def test_depth_2_traversal() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    e1, e2 = uuid.uuid4(), uuid.uuid4()
    nodes = {a: _mk_node(a), b: _mk_node(b), c: _mk_node(c)}
    edges = [_mk_edge(e1, a, b, GraphRelationType.supports), _mk_edge(e2, b, c, GraphRelationType.supports)]

    svc = GraphTraversalService(
        session=None,
        node_repo=_StubNodeRepo(nodes),
        edge_repo=_StubEdgeRepo(edges),
        node_ev_repo=_StubNodeEvRepo([]),
        edge_ev_repo=_StubEdgeEvRepo([]),
    )
    res = svc.neighborhood(start_node_id=a, depth=2, max_nodes=25, max_edges=50)
    assert {n.id for n in res.nodes} == {a, b, c}
    assert {e.id for e in res.edges} == {e1, e2}


def test_invalid_start_node() -> None:
    svc = GraphTraversalService(
        session=None,
        node_repo=_StubNodeRepo({}),
        edge_repo=_StubEdgeRepo([]),
        node_ev_repo=_StubNodeEvRepo([]),
        edge_ev_repo=_StubEdgeEvRepo([]),
    )
    with pytest.raises(GraphNodeNotFoundError):
        svc.neighborhood(start_node_id=uuid.uuid4())


def test_max_nodes_enforcement_no_edge_leak() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    e1, e2 = uuid.uuid4(), uuid.uuid4()
    nodes = {a: _mk_node(a), b: _mk_node(b), c: _mk_node(c)}
    edges = [_mk_edge(e1, a, b, GraphRelationType.supports), _mk_edge(e2, b, c, GraphRelationType.supports)]

    svc = GraphTraversalService(
        session=None,
        node_repo=_StubNodeRepo(nodes),
        edge_repo=_StubEdgeRepo(edges),
        node_ev_repo=_StubNodeEvRepo([]),
        edge_ev_repo=_StubEdgeEvRepo([]),
    )
    res = svc.neighborhood(start_node_id=a, depth=2, max_nodes=2, max_edges=50)
    assert {n.id for n in res.nodes} == {a, b}
    # Must not include B-C edge because C not included.
    assert {e.id for e in res.edges} == {e1}
    assert res.truncated
    assert "max_nodes_reached" in res.truncation_reasons


def test_max_edges_enforcement() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    e1, e2 = uuid.uuid4(), uuid.uuid4()
    nodes = {a: _mk_node(a), b: _mk_node(b), c: _mk_node(c)}
    edges = [_mk_edge(e1, a, b, GraphRelationType.supports), _mk_edge(e2, a, c, GraphRelationType.supports)]

    svc = GraphTraversalService(
        session=None,
        node_repo=_StubNodeRepo(nodes),
        edge_repo=_StubEdgeRepo(edges),
        node_ev_repo=_StubNodeEvRepo([]),
        edge_ev_repo=_StubEdgeEvRepo([]),
    )
    res = svc.neighborhood(start_node_id=a, depth=1, max_nodes=25, max_edges=1)
    assert len(res.edges) == 1
    assert res.truncated
    assert "max_edges_reached" in res.truncation_reasons


def test_relation_filter() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    e1, e2 = uuid.uuid4(), uuid.uuid4()
    nodes = {a: _mk_node(a), b: _mk_node(b)}
    edges = [
        _mk_edge(e1, a, b, GraphRelationType.supports),
        _mk_edge(e2, a, b, GraphRelationType.explains),
    ]
    svc = GraphTraversalService(
        session=None,
        node_repo=_StubNodeRepo(nodes),
        edge_repo=_StubEdgeRepo(edges),
        node_ev_repo=_StubNodeEvRepo([]),
        edge_ev_repo=_StubEdgeEvRepo([]),
    )
    res = svc.neighborhood(start_node_id=a, depth=1, relation_types=["supports"])
    assert {e.id for e in res.edges} == {e1}


def test_evidence_refs_included() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    e1 = uuid.uuid4()
    evu = uuid.uuid4()
    nodes = {a: _mk_node(a), b: _mk_node(b)}
    edges = [_mk_edge(e1, a, b, GraphRelationType.supports)]
    node_evs = [_NodeEv(graph_node_id=a, evidence_unit_id=evu, support_type="quote", confidence=0.9)]
    edge_evs = [_EdgeEv(graph_edge_id=e1, evidence_unit_id=evu, support_type="quote", confidence=0.8)]

    svc = GraphTraversalService(
        session=None,
        node_repo=_StubNodeRepo(nodes),
        edge_repo=_StubEdgeRepo(edges),
        node_ev_repo=_StubNodeEvRepo(node_evs),
        edge_ev_repo=_StubEdgeEvRepo(edge_evs),
    )
    res = svc.neighborhood(start_node_id=a, depth=1)
    assert res.node_evidence[0][0] == a
    assert res.edge_evidence[0][0] == e1

