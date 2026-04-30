from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.graph_node_evidence import GraphNodeEvidence
from app.repositories.evidence_unit_repository import EvidenceUnitRepository
from app.repositories.graph_node_evidence_repository import GraphNodeEvidenceRepository
from app.repositories.graph_node_repository import GraphNodeRepository
from app.services.errors import EvidenceUnitNotFoundError, GraphNodeEvidenceLinkAlreadyExistsError, GraphNodeNotFoundError


class GraphNodeEvidenceService:
    """Create evidence support links for graph nodes (Phase 3 Slice D).

    `support_type` validation is deferred to later slices; Phase 3 accepts any
    non-empty string enforced at the API schema level.
    """

    def __init__(self, *, session: Session) -> None:
        self._session = session
        self._node_repo = GraphNodeRepository(session)
        self._ev_repo = EvidenceUnitRepository(session)
        self._link_repo = GraphNodeEvidenceRepository(session)

    def attach(
        self,
        *,
        graph_node_id: uuid.UUID,
        evidence_unit_id: uuid.UUID,
        support_type: str,
        confidence: float | None,
        metadata: dict[str, Any] | None = None,
    ) -> GraphNodeEvidence:
        """Attach an EvidenceUnit to a GraphNode.

        This service does not commit; callers own transaction boundaries.
        """

        if self._node_repo.get(graph_node_id) is None:
            raise GraphNodeNotFoundError(f"GraphNode not found: {graph_node_id}")
        if self._ev_repo.get(evidence_unit_id) is None:
            raise EvidenceUnitNotFoundError(f"EvidenceUnit not found: {evidence_unit_id}")

        link = GraphNodeEvidence(
            graph_node_id=graph_node_id,
            evidence_unit_id=evidence_unit_id,
            support_type=support_type,
            confidence=confidence,
        )
        self._link_repo.add(link)
        try:
            # Flush so unique constraint violations can be surfaced deterministically.
            self._session.flush()
        except IntegrityError as e:
            raise GraphNodeEvidenceLinkAlreadyExistsError("graph_node_evidence_link_already_exists") from e

        _ = metadata  # reserved for future use; schema does not include metadata in Slice D.
        return link

