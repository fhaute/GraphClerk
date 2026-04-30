from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.enums import Modality, SourceFidelity
from app.models.evidence_unit import EvidenceUnit
from app.repositories.evidence_unit_repository import EvidenceUnitRepository
from app.services.evidence_selection_service import EvidenceSelectionService
from app.services.graph_traversal_service import GraphNeighborhood


def test_evidence_selection_prefers_verbatim_and_dedupes() -> None:
    session = MagicMock(spec=Session)
    eu_verbatim = uuid.uuid4()
    eu_derived = uuid.uuid4()
    node_id = uuid.uuid4()

    repo = MagicMock(spec=EvidenceUnitRepository)

    now = datetime.now(timezone.utc)

    def list_by_ids(ids: list[uuid.UUID]):
        units = []
        for i in ids:
            if i == eu_verbatim:
                units.append(
                    EvidenceUnit(
                        id=i,
                        artifact_id=uuid.uuid4(),
                        modality=Modality.text,
                        content_type="paragraph",
                        text="same",
                        location=None,
                        source_fidelity=SourceFidelity.verbatim,
                        confidence=0.5,
                        metadata_json=None,
                        created_at=now,
                        updated_at=now,
                    )
                )
            else:
                units.append(
                    EvidenceUnit(
                        id=i,
                        artifact_id=uuid.uuid4(),
                        modality=Modality.text,
                        content_type="paragraph",
                        text="same",
                        location=None,
                        source_fidelity=SourceFidelity.derived,
                        confidence=0.9,
                        metadata_json=None,
                        created_at=now,
                        updated_at=now,
                    )
                )
        return units

    repo.list_by_ids.side_effect = list_by_ids

    node = MagicMock()
    node.id = node_id

    nh = GraphNeighborhood(
        start_node_id=node_id,
        depth=1,
        max_nodes=10,
        max_edges=10,
        relation_types=None,
        truncated=False,
        truncation_reasons=[],
        nodes=[node],
        edges=[],
        node_evidence=[(node_id, eu_derived, "supports", 0.1), (node_id, eu_verbatim, "supports", 0.2)],
        edge_evidence=[],
    )

    svc = EvidenceSelectionService(session=session, evidence_repo=repo)
    ranked = svc.collect_from_neighborhoods([nh])
    assert [c.evidence_unit_id for c in ranked] == [eu_verbatim, eu_derived]
