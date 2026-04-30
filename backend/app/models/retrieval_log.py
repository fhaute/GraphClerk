from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RetrievalLog(Base):
    """Persistence model for retrieval traces (observability only in Phase 1)."""

    __tablename__ = "retrieval_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    question: Mapped[str] = mapped_column(Text)
    selected_indexes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    graph_path: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    evidence_unit_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    confidence: Mapped[float | None] = mapped_column(nullable=True)
    warnings: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

