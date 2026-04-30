from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.graph_edge_evidence import GraphEdgeEvidence
from app.repositories.evidence_unit_repository import EvidenceUnitRepository
from app.repositories.graph_edge_evidence_repository import GraphEdgeEvidenceRepository
from app.repositories.graph_edge_repository import GraphEdgeRepository
from app.services.errors import EvidenceUnitNotFoundError, GraphEdgeEvidenceLinkAlreadyExistsError, GraphEdgeNotFoundError


class GraphEdgeEvidenceService:
    """Create evidence support links for graph edges (Phase 3 Slice D).

    `support_type` validation is deferred to later slices; Phase 3 accepts any
    non-empty string enforced at the API schema level.
    """

    def __init__(self, *, session: Session) -> None:
        self._session = session
        self._edge_repo = GraphEdgeRepository(session)
        self._ev_repo = EvidenceUnitRepository(session)
        self._link_repo = GraphEdgeEvidenceRepository(session)

    def attach(
        self,
        *,
        graph_edge_id: uuid.UUID,
        evidence_unit_id: uuid.UUID,
        support_type: str,
        confidence: float | None,
        metadata: dict[str, Any] | None = None,
    ) -> GraphEdgeEvidence:
        """Attach an EvidenceUnit to a GraphEdge.

        This service does not commit; callers own transaction boundaries.
        """

        if self._edge_repo.get(graph_edge_id) is None:
            raise GraphEdgeNotFoundError(f"GraphEdge not found: {graph_edge_id}")
        if self._ev_repo.get(evidence_unit_id) is None:
            raise EvidenceUnitNotFoundError(f"EvidenceUnit not found: {evidence_unit_id}")

        link = GraphEdgeEvidence(
            graph_edge_id=graph_edge_id,
            evidence_unit_id=evidence_unit_id,
            support_type=support_type,
            confidence=confidence,
        )
        self._link_repo.add(link)
        try:
            self._session.flush()
        except IntegrityError as e:
            raise GraphEdgeEvidenceLinkAlreadyExistsError("graph_edge_evidence_link_already_exists") from e

        _ = metadata
        return link

