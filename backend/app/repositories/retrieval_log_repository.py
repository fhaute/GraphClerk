"""Persistence helpers for `RetrievalLog` (Phase 4)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.retrieval_log import RetrievalLog
from app.schemas.retrieval_packet import RetrievalPacket


class RetrievalLogRepository:
    """Write retrieval traces including canonical packet snapshots."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_from_packet(
        self,
        *,
        packet: RetrievalPacket,
        latency_ms: int,
        token_estimate: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> uuid.UUID:
        """Persist a retrieval log row; returns the new log id."""

        meta: dict[str, Any] = dict(metadata or {})
        meta["interpreted_intent"] = packet.interpreted_intent.model_dump(mode="json")
        meta["alternative_interpretations_count"] = len(packet.alternative_interpretations)

        log = RetrievalLog(
            question=packet.question,
            selected_indexes=[x.model_dump(mode="json") for x in packet.selected_indexes] or None,
            graph_path={"paths": [p.model_dump(mode="json") for p in packet.graph_paths]} if packet.graph_paths else None,
            evidence_unit_ids=[e.evidence_unit_id for e in packet.evidence_units] or None,
            confidence=packet.confidence,
            warnings=list(packet.warnings) or None,
            latency_ms=latency_ms,
            token_estimate=token_estimate,
            metadata_json=meta,
            retrieval_packet=packet.model_dump(mode="json"),
        )
        self._session.add(log)
        self._session.flush()
        return log.id
