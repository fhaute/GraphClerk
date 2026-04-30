from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from app.services.errors import EmbeddingAdapterNotConfiguredError, EmbeddingGenerationError


class EmbeddingAdapter(Protocol):
    """Generate vector embeddings for searchable text.

    Phase 3 uses an adapter interface to avoid hard-coding any embedding provider.
    Implementations must fail explicitly rather than returning fake success.
    """

    dimension: int

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for the provided text."""


@dataclass(frozen=True)
class DeterministicFakeEmbeddingAdapter:
    """Visibly fake embedding adapter for tests/dev only.

    This implementation is intentionally NOT a semantic embedding model.
    It uses a stable sha256-based method to produce deterministic vectors for
    the same input text across processes.
    """

    dimension: int = 8

    def embed_text(self, text: str) -> list[float]:
        try:
            # Stable digest across processes and platforms.
            digest = hashlib.sha256(text.encode("utf-8")).digest()
        except Exception as e:
            raise EmbeddingGenerationError(str(e)) from e

        # Expand digest deterministically to required dimension by re-hashing.
        out: list[float] = []
        counter = 0
        while len(out) < self.dimension:
            block = hashlib.sha256(digest + counter.to_bytes(4, "big")).digest()
            # Convert bytes to floats in [0, 1] using uint32 chunks.
            for i in range(0, len(block), 4):
                if len(out) >= self.dimension:
                    break
                u = int.from_bytes(block[i : i + 4], "big", signed=False)
                out.append(u / 2**32)
            counter += 1
        return out


@dataclass(frozen=True)
class NotConfiguredEmbeddingAdapter:
    """Explicit placeholder adapter used when embeddings are not wired yet."""

    dimension: int = 0

    def embed_text(self, text: str) -> list[float]:
        _ = text
        raise EmbeddingAdapterNotConfiguredError("embedding_adapter_not_configured")

