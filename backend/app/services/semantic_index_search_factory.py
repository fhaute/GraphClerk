"""Shared wiring for `SemanticIndexSearchService` (Phase 4).

Keeps `GET /semantic-indexes/search` behavior aligned with File Clerk route selection
by centralizing construction of embedding + vector + search service dependencies.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.semantic_index_search_service import SemanticIndexSearchService


def build_semantic_index_search_service(*, session: Session) -> SemanticIndexSearchService:
    """Construct the default Phase 3 semantic index search stack for a DB session.

    When ``GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER=deterministic_fake`` (allowed only
    under ``Settings`` validation rules), embeddings are **non-semantic** test vectors —
    not a production embedding capability.
    """

    from qdrant_client import QdrantClient

    from app.core.config import get_settings
    from app.services.embedding_adapter import NotConfiguredEmbeddingAdapter
    from app.services.embedding_service import EmbeddingService
    from app.services.vector_index_service import VectorIndexService

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    # Phase 3 / Track B: explicit expected dimension (must match B1 backfill script and deterministic fake).
    expected_dimension = 8
    if settings.semantic_search_embedding_adapter == "deterministic_fake":
        from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter

        embedding = EmbeddingService(
            adapter=DeterministicFakeEmbeddingAdapter(dimension=expected_dimension),
            expected_dimension=expected_dimension,
        )
    else:
        embedding = EmbeddingService(
            adapter=NotConfiguredEmbeddingAdapter(dimension=expected_dimension),
            expected_dimension=expected_dimension,
        )
    vector = VectorIndexService(qdrant_client=client, expected_dimension=expected_dimension)
    return SemanticIndexSearchService(session=session, embedding_service=embedding, vector_index_service=vector)
