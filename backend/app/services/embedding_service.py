from __future__ import annotations

import math
from typing import Iterable

from app.services.embedding_adapter import EmbeddingAdapter
from app.services.errors import (
    EmbeddingDimensionMismatchError,
    EmbeddingInvalidVectorError,
    EmbeddingTextEmptyError,
)


class EmbeddingService:
    """Embedding orchestration + validation (Phase 3 Slice F).

    This service does not talk to Qdrant and does not persist anything.
    """

    def __init__(self, *, adapter: EmbeddingAdapter, expected_dimension: int) -> None:
        self._adapter = adapter
        self._expected_dimension = expected_dimension

    def embed_text(self, text: str) -> list[float]:
        if text.strip() == "":
            raise EmbeddingTextEmptyError("embedding_text_empty")

        vec = self._adapter.embed_text(text)

        if not isinstance(vec, list):
            # Keep this strict so callers don't accidentally pass numpy arrays, etc.
            raise EmbeddingInvalidVectorError("embedding_vector_not_list")

        if len(vec) != self._expected_dimension:
            raise EmbeddingDimensionMismatchError(
                f"embedding_dimension_mismatch expected={self._expected_dimension} got={len(vec)}"
            )

        out: list[float] = []
        for v in vec:
            try:
                f = float(v)
            except Exception as e:
                raise EmbeddingInvalidVectorError("embedding_vector_non_numeric") from e
            if not math.isfinite(f):
                raise EmbeddingInvalidVectorError("embedding_vector_non_finite")
            out.append(f)

        return out

