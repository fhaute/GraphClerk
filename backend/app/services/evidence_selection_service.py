"""Evidence selection from graph support links only (Phase 4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import SourceFidelity
from app.repositories.evidence_unit_repository import EvidenceUnitRepository
from app.services.graph_traversal_service import GraphNeighborhood


@dataclass(frozen=True)
class EvidenceCandidate:
    """Ranked evidence candidate with traceability to graph support."""

    evidence_unit_id: uuid.UUID
    artifact_id: uuid.UUID
    modality: str
    content_type: str
    source_fidelity: str
    text: str | None
    location: dict | None
    unit_confidence: float | None
    support_confidence: float | None
    selection_reason: str


class EvidenceSelectionService:
    """Load and rank `EvidenceUnit` rows referenced by graph node/edge evidence links."""

    _FIDELITY_ORDER: tuple[str, ...] = (
        str(SourceFidelity.verbatim),
        str(SourceFidelity.extracted),
        str(SourceFidelity.derived),
        str(SourceFidelity.computed),
    )

    def __init__(self, *, session: Session, evidence_repo: EvidenceUnitRepository | None = None) -> None:
        self._session = session
        self._evidence_repo = evidence_repo or EvidenceUnitRepository(session)

    def _fidelity_rank(self, fidelity: str) -> int:
        try:
            return self._FIDELITY_ORDER.index(fidelity)
        except ValueError:
            return len(self._FIDELITY_ORDER)

    def collect_from_neighborhoods(self, neighborhoods: list[GraphNeighborhood]) -> list[EvidenceCandidate]:
        """Collect evidence candidates from traversal neighborhoods (support links only)."""

        link_meta: dict[uuid.UUID, tuple[float | None, str]] = {}

        for nh in neighborhoods:
            for node_id, eu_id, _support_type, conf in nh.node_evidence:
                reason = f"Linked from graph node {node_id} in neighborhood of {nh.start_node_id}."
                self._maybe_upgrade_link(link_meta, eu_id, conf, reason)
            for edge_id, eu_id, _support_type, conf in nh.edge_evidence:
                reason = f"Linked from graph edge {edge_id} in neighborhood of {nh.start_node_id}."
                self._maybe_upgrade_link(link_meta, eu_id, conf, reason)

        if not link_meta:
            return []

        units = self._evidence_repo.list_by_ids(list(link_meta.keys()))
        by_id = {u.id: u for u in units}

        candidates: list[EvidenceCandidate] = []
        for eu_id, (support_conf, reason) in link_meta.items():
            u = by_id.get(eu_id)
            if u is None:
                continue
            candidates.append(
                EvidenceCandidate(
                    evidence_unit_id=u.id,
                    artifact_id=u.artifact_id,
                    modality=str(u.modality),
                    content_type=u.content_type,
                    source_fidelity=str(u.source_fidelity),
                    text=u.text,
                    location=u.location,
                    unit_confidence=u.confidence,
                    support_confidence=support_conf,
                    selection_reason=reason,
                )
            )

        candidates.sort(
            key=lambda c: (
                self._fidelity_rank(c.source_fidelity),
                -(c.support_confidence or c.unit_confidence or 0.0),
                str(c.evidence_unit_id),
            )
        )

        # Dedupe by evidence id while preserving order (already sorted).
        seen: set[uuid.UUID] = set()
        deduped: list[EvidenceCandidate] = []
        for c in candidates:
            if c.evidence_unit_id in seen:
                continue
            seen.add(c.evidence_unit_id)
            deduped.append(c)
        return deduped

    @staticmethod
    def _maybe_upgrade_link(
        link_meta: dict[uuid.UUID, tuple[float | None, str]],
        evidence_unit_id: uuid.UUID,
        support_conf: float | None,
        reason: str,
    ) -> None:
        prev = link_meta.get(evidence_unit_id)
        if prev is None:
            link_meta[evidence_unit_id] = (support_conf, reason)
            return
        prev_conf, prev_reason = prev
        new_conf = support_conf if support_conf is not None else prev_conf
        if prev_conf is None or (support_conf is not None and support_conf > prev_conf):
            link_meta[evidence_unit_id] = (new_conf, reason)
            return
        link_meta[evidence_unit_id] = (prev_conf, prev_reason)
