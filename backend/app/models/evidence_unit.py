from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Modality, SourceFidelity


class EvidenceUnit(Base):
    """Persistence model for a source-backed evidence unit.

    Phase 1 defines schema only; it does not implement real extraction from files.
    """

    __tablename__ = "evidence_unit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifact.id", ondelete="RESTRICT"),
        index=True,
    )

    modality: Mapped[Modality] = mapped_column(String(32))
    content_type: Mapped[str] = mapped_column(String(64))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    source_fidelity: Mapped[SourceFidelity] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    artifact = relationship("Artifact", lazy="joined")

