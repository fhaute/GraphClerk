from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import SemanticIndexVectorStatus


class SemanticIndex(Base):
    """Persistence model for a searchable meaning entry point into the graph.

    Phase 1: no embeddings are generated; this is schema-only.

    Phase 3+: `entry_node_ids` is legacy and must not be treated as the source of truth.
    The normalized `semantic_index_entry_node` join table is the source of truth for
    entry nodes.
    """

    __tablename__ = "semantic_index"
    __table_args__ = (
        CheckConstraint(
            "vector_status IN ('pending','indexed','failed')",
            name="ck_semantic_index_vector_status_allowed",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    meaning: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Persistence shape only. Phase 1 does not define link tables yet.
    entry_node_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    vector_status: Mapped[SemanticIndexVectorStatus] = mapped_column(
        String(16),
        default=SemanticIndexVectorStatus.pending,
    )

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

