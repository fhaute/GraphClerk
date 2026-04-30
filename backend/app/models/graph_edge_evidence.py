from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GraphEdgeEvidence(Base):
    """Support link between a GraphEdge and an EvidenceUnit.

    Phase 3 schema only. `support_type` validation is service-level behavior in later slices.
    """

    __tablename__ = "graph_edge_evidence"
    __table_args__ = (
        UniqueConstraint(
            "graph_edge_id",
            "evidence_unit_id",
            "support_type",
            name="uq_graph_edge_evidence_edge_ev_support",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    graph_edge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_edge.id", ondelete="RESTRICT"),
        index=True,
    )
    evidence_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_unit.id", ondelete="RESTRICT"),
        index=True,
    )

    support_type: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

