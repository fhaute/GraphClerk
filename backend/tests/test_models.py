from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    Artifact,
    EvidenceUnit,
    GraphEdge,
    GraphEdgeEvidence,
    GraphNode,
    GraphNodeEvidence,
    RetrievalLog,
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


def _require_database_url() -> str:
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set; skipping persistence model tests.")
    return database_url


def _db_session() -> Session:
    engine = create_engine(_require_database_url(), pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_artifact_model_creation() -> None:
    with _db_session() as session:
        a = Artifact(
            filename="a.md",
            title="A",
            artifact_type="markdown",
            mime_type="text/markdown",
            storage_uri="file:///a.md",
            checksum=None,
            size_bytes=123,
            raw_text=None,
            metadata_json={"k": "v"},
        )
        session.add(a)
        session.commit()

        assert a.id is not None


def test_evidence_unit_model_creation() -> None:
    with _db_session() as session:
        a = Artifact(
            filename="a.pdf",
            title=None,
            artifact_type="pdf",
            mime_type="application/pdf",
            storage_uri="file:///a.pdf",
            checksum="abc",
            size_bytes=456,
            raw_text=None,
            metadata_json=None,
        )
        session.add(a)
        session.flush()

        e = EvidenceUnit(
            artifact_id=a.id,
            modality=Modality.pdf,
            content_type="paragraph",
            text="hello",
            location={"page": 1},
            source_fidelity=SourceFidelity.extracted,
            confidence=0.9,
            metadata_json=None,
        )
        session.add(e)
        session.commit()

        assert e.id is not None


def test_graph_node_model_creation() -> None:
    with _db_session() as session:
        n = GraphNode(node_type=GraphNodeType.concept, label="RAG", summary=None, metadata_json=None)
        session.add(n)
        session.commit()
        assert n.id is not None


def test_graph_edge_model_creation() -> None:
    with _db_session() as session:
        a = GraphNode(node_type=GraphNodeType.concept, label="A", summary=None, metadata_json=None)
        b = GraphNode(node_type=GraphNodeType.concept, label="B", summary=None, metadata_json=None)
        session.add_all([a, b])
        session.flush()

        e = GraphEdge(
            from_node_id=a.id,
            to_node_id=b.id,
            relation_type=GraphRelationType.related_to,
            summary=None,
            confidence=0.7,
            metadata_json=None,
        )
        session.add(e)
        session.commit()
        assert e.id is not None


def test_semantic_index_model_creation() -> None:
    with _db_session() as session:
        si = SemanticIndex(
            meaning="meaning",
            summary="summary",
            embedding_text="embedding text",
            entry_node_ids=None,
            vector_status=SemanticIndexVectorStatus.pending,
            metadata_json=None,
        )
        session.add(si)
        session.commit()
        assert si.id is not None


def test_semantic_index_vector_status_default_pending() -> None:
    with _db_session() as session:
        si = SemanticIndex(
            meaning="meaning",
            summary=None,
            embedding_text=None,
            entry_node_ids=None,
            metadata_json=None,
        )
        session.add(si)
        session.commit()
        assert si.vector_status == SemanticIndexVectorStatus.pending


def test_semantic_index_vector_status_rejects_invalid_value() -> None:
    with _db_session() as session:
        si = SemanticIndex(
            meaning="meaning",
            summary=None,
            embedding_text=None,
            entry_node_ids=None,
            vector_status="bogus",  # type: ignore[arg-type]
            metadata_json=None,
        )
        session.add(si)
        with pytest.raises(Exception):
            session.commit()


def test_retrieval_log_model_creation() -> None:
    with _db_session() as session:
        rl = RetrievalLog(
            question="q",
            selected_indexes=None,
            graph_path=None,
            evidence_unit_ids=None,
            confidence=None,
            warnings=["w"],
            latency_ms=12,
            token_estimate=34,
            metadata_json=None,
        )
        session.add(rl)
        session.commit()
        assert rl.id is not None


def test_graph_edge_requires_valid_nodes() -> None:
    with _db_session() as session:
        bogus_id = "00000000-0000-0000-0000-000000000000"
        e = GraphEdge(
            from_node_id=bogus_id,  # type: ignore[arg-type]
            to_node_id=bogus_id,  # type: ignore[arg-type]
            relation_type=GraphRelationType.related_to,
            summary=None,
            confidence=None,
            metadata_json=None,
        )
        session.add(e)
        with pytest.raises(Exception):
            session.commit()


def test_evidence_unit_requires_artifact() -> None:
    with _db_session() as session:
        bogus_id = "00000000-0000-0000-0000-000000000000"
        e = EvidenceUnit(
            artifact_id=bogus_id,  # type: ignore[arg-type]
            modality=Modality.text,
            content_type="paragraph",
            text="hello",
            location=None,
            source_fidelity=SourceFidelity.verbatim,
            confidence=None,
            metadata_json=None,
        )
        session.add(e)
        with pytest.raises(Exception):
            session.commit()


def test_semantic_index_entry_node_requires_valid_ids() -> None:
    with _db_session() as session:
        bogus_id = "00000000-0000-0000-0000-000000000000"
        link = SemanticIndexEntryNode(
            semantic_index_id=bogus_id,  # type: ignore[arg-type]
            graph_node_id=bogus_id,  # type: ignore[arg-type]
        )
        session.add(link)
        with pytest.raises(Exception):
            session.commit()


def test_semantic_index_entry_node_duplicate_rejected() -> None:
    with _db_session() as session:
        n = GraphNode(node_type=GraphNodeType.concept, label="N", summary=None, metadata_json=None)
        si = SemanticIndex(meaning="m", summary=None, embedding_text=None, entry_node_ids=None, metadata_json=None)
        session.add_all([n, si])
        session.flush()

        a = SemanticIndexEntryNode(semantic_index_id=si.id, graph_node_id=n.id)
        b = SemanticIndexEntryNode(semantic_index_id=si.id, graph_node_id=n.id)
        session.add_all([a, b])
        with pytest.raises(Exception):
            session.commit()


def test_graph_node_evidence_requires_valid_ids() -> None:
    with _db_session() as session:
        bogus_id = "00000000-0000-0000-0000-000000000000"
        link = GraphNodeEvidence(
            graph_node_id=bogus_id,  # type: ignore[arg-type]
            evidence_unit_id=bogus_id,  # type: ignore[arg-type]
            support_type="supports",
            confidence=None,
        )
        session.add(link)
        with pytest.raises(Exception):
            session.commit()


def test_graph_node_evidence_duplicate_rejected() -> None:
    with _db_session() as session:
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
        n = GraphNode(node_type=GraphNodeType.concept, label="N", summary=None, metadata_json=None)
        session.add_all([ev, n])
        session.flush()

        x = GraphNodeEvidence(graph_node_id=n.id, evidence_unit_id=ev.id, support_type="supports", confidence=None)
        y = GraphNodeEvidence(graph_node_id=n.id, evidence_unit_id=ev.id, support_type="supports", confidence=None)
        session.add_all([x, y])
        with pytest.raises(Exception):
            session.commit()


def test_graph_edge_evidence_requires_valid_ids() -> None:
    with _db_session() as session:
        bogus_id = "00000000-0000-0000-0000-000000000000"
        link = GraphEdgeEvidence(
            graph_edge_id=bogus_id,  # type: ignore[arg-type]
            evidence_unit_id=bogus_id,  # type: ignore[arg-type]
            support_type="supports",
            confidence=None,
        )
        session.add(link)
        with pytest.raises(Exception):
            session.commit()


def test_graph_edge_evidence_duplicate_rejected() -> None:
    with _db_session() as session:
        n1 = GraphNode(node_type=GraphNodeType.concept, label="A", summary=None, metadata_json=None)
        n2 = GraphNode(node_type=GraphNodeType.concept, label="B", summary=None, metadata_json=None)
        session.add_all([n1, n2])
        session.flush()

        edge = GraphEdge(
            from_node_id=n1.id,
            to_node_id=n2.id,
            relation_type=GraphRelationType.related_to,
            summary=None,
            confidence=None,
            metadata_json=None,
        )
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
        session.add_all([edge, a])
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
        session.flush()

        x = GraphEdgeEvidence(graph_edge_id=edge.id, evidence_unit_id=ev.id, support_type="supports", confidence=None)
        y = GraphEdgeEvidence(graph_edge_id=edge.id, evidence_unit_id=ev.id, support_type="supports", confidence=None)
        session.add_all([x, y])
        with pytest.raises(Exception):
            session.commit()

