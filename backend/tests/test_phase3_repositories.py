from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Artifact,
    EvidenceUnit,
    GraphEdge,
    GraphEdgeEvidence,
    GraphNode,
    GraphNodeEvidence,
    SemanticIndex,
    SemanticIndexEntryNode,
)
from app.models.enums import (
    GraphNodeType,
    GraphRelationType,
    Modality,
    SemanticIndexVectorStatus,
    SourceFidelity,
)
from app.repositories.graph_edge_evidence_repository import GraphEdgeEvidenceRepository
from app.repositories.graph_edge_repository import GraphEdgeRepository
from app.repositories.graph_node_evidence_repository import GraphNodeEvidenceRepository
from app.repositories.graph_node_repository import GraphNodeRepository
from app.repositories.semantic_index_entry_node_repository import SemanticIndexEntryNodeRepository
from app.repositories.semantic_index_repository import SemanticIndexRepository


def _session() -> Session:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


def test_graph_node_repository_add_get_list(db_ready: None) -> None:
    with _session() as session:
        repo = GraphNodeRepository(session)
        n = GraphNode(node_type=GraphNodeType.concept, label="N", summary=None, metadata_json=None)
        repo.add(n)
        session.commit()

        got = repo.get(n.id)
        assert got is not None
        assert got.id == n.id

        items = repo.list(limit=10, offset=0)
        assert any(x.id == n.id for x in items)


def test_graph_edge_repository_add_get_list_by_node(db_ready: None) -> None:
    with _session() as session:
        nodes = GraphNodeRepository(session)
        edges = GraphEdgeRepository(session)

        a = GraphNode(node_type=GraphNodeType.concept, label="A", summary=None, metadata_json=None)
        b = GraphNode(node_type=GraphNodeType.concept, label="B", summary=None, metadata_json=None)
        nodes.add(a)
        nodes.add(b)
        session.flush()

        e = GraphEdge(
            from_node_id=a.id,
            to_node_id=b.id,
            relation_type=GraphRelationType.related_to,
            summary=None,
            confidence=None,
            metadata_json=None,
        )
        edges.add(e)
        session.commit()

        got = edges.get(e.id)
        assert got is not None
        assert got.id == e.id

        by_a = edges.list_by_node(a.id)
        assert any(x.id == e.id for x in by_a)

        by_b = edges.list_by_node(b.id)
        assert any(x.id == e.id for x in by_b)


def test_graph_node_evidence_repository_add_list_by_graph_node(db_ready: None) -> None:
    with _session() as session:
        node_repo = GraphNodeRepository(session)
        link_repo = GraphNodeEvidenceRepository(session)

        a = Artifact(
            filename="a.txt",
            title=None,
            artifact_type="text",
            mime_type="text/plain",
            storage_uri="file:///a.txt",
            checksum="abc",
            size_bytes=1,
            raw_text="A",
            metadata_json=None,
        )
        session.add(a)
        session.flush()
        ev = EvidenceUnit(
            artifact_id=a.id,
            modality=Modality.text,
            content_type="paragraph",
            text="A",
            location=None,
            source_fidelity=SourceFidelity.verbatim,
            confidence=None,
            metadata_json=None,
        )
        session.add(ev)

        n = GraphNode(node_type=GraphNodeType.concept, label="N", summary=None, metadata_json=None)
        node_repo.add(n)
        session.flush()

        link = GraphNodeEvidence(graph_node_id=n.id, evidence_unit_id=ev.id, support_type="supports", confidence=None)
        link_repo.add(link)
        session.commit()

        got = link_repo.get(link.id)
        assert got is not None
        assert got.id == link.id

        by_node = link_repo.list_by_graph_node(n.id)
        assert any(x.id == link.id for x in by_node)

        by_ev = link_repo.list_by_evidence_unit(ev.id)
        assert any(x.id == link.id for x in by_ev)


def test_graph_edge_evidence_repository_add_list_by_graph_edge(db_ready: None) -> None:
    with _session() as session:
        node_repo = GraphNodeRepository(session)
        edge_repo = GraphEdgeRepository(session)
        link_repo = GraphEdgeEvidenceRepository(session)

        a = GraphNode(node_type=GraphNodeType.concept, label="A", summary=None, metadata_json=None)
        b = GraphNode(node_type=GraphNodeType.concept, label="B", summary=None, metadata_json=None)
        node_repo.add(a)
        node_repo.add(b)
        session.flush()

        edge = GraphEdge(
            from_node_id=a.id,
            to_node_id=b.id,
            relation_type=GraphRelationType.related_to,
            summary=None,
            confidence=None,
            metadata_json=None,
        )
        edge_repo.add(edge)

        art = Artifact(
            filename="a.txt",
            title=None,
            artifact_type="text",
            mime_type="text/plain",
            storage_uri="file:///a.txt",
            checksum="abc",
            size_bytes=1,
            raw_text="A",
            metadata_json=None,
        )
        session.add(art)
        session.flush()
        ev = EvidenceUnit(
            artifact_id=art.id,
            modality=Modality.text,
            content_type="paragraph",
            text="A",
            location=None,
            source_fidelity=SourceFidelity.verbatim,
            confidence=None,
            metadata_json=None,
        )
        session.add(ev)
        session.flush()

        link = GraphEdgeEvidence(graph_edge_id=edge.id, evidence_unit_id=ev.id, support_type="supports", confidence=None)
        link_repo.add(link)
        session.commit()

        got = link_repo.get(link.id)
        assert got is not None
        assert got.id == link.id

        by_edge = link_repo.list_by_graph_edge(edge.id)
        assert any(x.id == link.id for x in by_edge)

        by_ev = link_repo.list_by_evidence_unit(ev.id)
        assert any(x.id == link.id for x in by_ev)


def test_semantic_index_repository_add_get_list_by_vector_status(db_ready: None) -> None:
    with _session() as session:
        repo = SemanticIndexRepository(session)

        idx = SemanticIndex(
            meaning="m",
            summary=None,
            embedding_text=None,
            entry_node_ids=None,
            vector_status=SemanticIndexVectorStatus.pending,
            metadata_json=None,
        )
        repo.add(idx)
        session.commit()

        got = repo.get(idx.id)
        assert got is not None
        assert got.id == idx.id

        items = repo.list_by_vector_status(SemanticIndexVectorStatus.pending, limit=100, offset=0)
        assert any(x.id == idx.id for x in items)


def test_semantic_index_entry_node_repository_add_get_list(db_ready: None) -> None:
    with _session() as session:
        node_repo = GraphNodeRepository(session)
        idx_repo = SemanticIndexRepository(session)
        link_repo = SemanticIndexEntryNodeRepository(session)

        n = GraphNode(node_type=GraphNodeType.concept, label="N", summary=None, metadata_json=None)
        node_repo.add(n)

        idx = SemanticIndex(
            meaning="m",
            summary=None,
            embedding_text=None,
            entry_node_ids=None,
            vector_status=SemanticIndexVectorStatus.pending,
            metadata_json=None,
        )
        idx_repo.add(idx)
        session.flush()

        link = SemanticIndexEntryNode(semantic_index_id=idx.id, graph_node_id=n.id)
        link_repo.add(link)
        session.commit()

        got = link_repo.get(link.id)
        assert got is not None
        assert got.id == link.id

        by_idx = link_repo.list_by_semantic_index(idx.id, limit=1000, offset=0)
        assert any(x.id == link.id for x in by_idx)

        by_node = link_repo.list_by_graph_node(n.id, limit=1000, offset=0)
        assert any(x.id == link.id for x in by_node)

