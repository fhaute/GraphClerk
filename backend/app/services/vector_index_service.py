from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from app.services.errors import (
    VectorIndexDimensionMismatchError,
    VectorIndexOperationError,
    VectorIndexUnavailableError,
)


@dataclass(frozen=True)
class _FallbackVectorParams:
    """Fallback stand-in for qdrant_client.http.models.VectorParams (tests only)."""

    size: int
    distance: str


@dataclass(frozen=True)
class _FallbackPointStruct:
    """Fallback stand-in for qdrant_client.http.models.PointStruct (tests only)."""

    id: str
    vector: list[float]
    payload: dict[str, Any]



@dataclass(frozen=True)
class SearchHit:
    """Normalized vector search hit (Phase 3 Slice G)."""

    semantic_index_id: uuid.UUID
    score: float
    payload: dict[str, Any]


class _QdrantClientLike(Protocol):
    """Minimal Qdrant client surface used by VectorIndexService."""

    def get_collection(self, collection_name: str) -> Any: ...

    def create_collection(self, collection_name: str, vectors_config: Any) -> Any: ...

    def upsert(self, collection_name: str, points: Any) -> Any: ...

    def search(self, collection_name: str, query_vector: list[float], limit: int) -> Any: ...


class VectorIndexService:
    """Vector index access for SemanticIndexes via Qdrant (Phase 3 Slice G only).

    - Collection name: `semantic_indexes`
    - Distance: cosine
    - Point ID strategy: use `semantic_index_id` as a **string point id** for stability.
      (Qdrant point IDs support string ids via qdrant-client; we avoid inventing any mapping.)

    Qdrant payload is convenience metadata only. Postgres remains the source of truth.
    """

    collection_name = "semantic_indexes"

    def __init__(self, *, qdrant_client: _QdrantClientLike, expected_dimension: int) -> None:
        self._client = qdrant_client
        self._expected_dimension = expected_dimension

    def ensure_semantic_indexes_collection(self) -> None:
        """Create the semantic_indexes collection if it does not exist."""

        try:
            self._client.get_collection(self.collection_name)
            return
        except Exception as e:
            # If the collection doesn't exist, Qdrant raises; try to create.
            try:
                try:
                    from qdrant_client.http.models import Distance, VectorParams

                    vectors_config: Any = VectorParams(
                        size=self._expected_dimension,
                        distance=Distance.COSINE,
                    )
                except ModuleNotFoundError:
                    # Unit tests may run without qdrant-client installed.
                    vectors_config = _FallbackVectorParams(size=self._expected_dimension, distance="COSINE")

                self._client.create_collection(collection_name=self.collection_name, vectors_config=vectors_config)
            except Exception as create_e:
                # If create also fails, treat it as unavailable/misconfigured.
                raise VectorIndexUnavailableError(str(create_e)) from create_e

    def upsert_semantic_index_vector(
        self,
        *,
        semantic_index_id: uuid.UUID,
        vector: list[float],
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Upsert a SemanticIndex vector into Qdrant."""

        self._validate_vector(vector)
        try:
            try:
                from qdrant_client.http.models import PointStruct

                point: Any = PointStruct(
                    id=str(semantic_index_id),
                    vector=vector,
                    payload={"semantic_index_id": str(semantic_index_id), **(payload or {})},
                )
            except ModuleNotFoundError:
                point = _FallbackPointStruct(
                    id=str(semantic_index_id),
                    vector=vector,
                    payload={"semantic_index_id": str(semantic_index_id), **(payload or {})},
                )
            self._client.upsert(collection_name=self.collection_name, points=[point])
        except VectorIndexDimensionMismatchError:
            raise
        except Exception as e:
            raise VectorIndexOperationError(str(e)) from e

    def search_semantic_indexes(self, *, query_vector: list[float], limit: int = 5) -> list[SearchHit]:
        """Search for semantic indexes by vector similarity."""

        self._validate_vector(query_vector)
        try:
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
            )
        except VectorIndexDimensionMismatchError:
            raise
        except Exception as e:
            raise VectorIndexUnavailableError(str(e)) from e

        hits: list[SearchHit] = []
        for r in results:
            payload = getattr(r, "payload", None)
            score = getattr(r, "score", None)
            if not isinstance(payload, dict):
                raise VectorIndexOperationError("malformed_search_result_payload")
            if score is None:
                raise VectorIndexOperationError("malformed_search_result_score")
            raw_id = payload.get("semantic_index_id")
            if not isinstance(raw_id, str):
                raise VectorIndexOperationError("missing_semantic_index_id_in_payload")
            try:
                sid = uuid.UUID(raw_id)
            except Exception as e:
                raise VectorIndexOperationError("malformed_semantic_index_id_in_payload") from e
            hits.append(SearchHit(semantic_index_id=sid, score=float(score), payload=payload))
        return hits

    def _validate_vector(self, vector: list[float]) -> None:
        if not isinstance(vector, list):
            raise VectorIndexDimensionMismatchError("vector_not_list")
        if len(vector) != self._expected_dimension:
            raise VectorIndexDimensionMismatchError(
                f"vector_dimension_mismatch expected={self._expected_dimension} got={len(vector)}"
            )
