from __future__ import annotations

import pytest

from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter, NotConfiguredEmbeddingAdapter
from app.services.embedding_service import EmbeddingService
from app.services.errors import (
    EmbeddingAdapterNotConfiguredError,
    EmbeddingDimensionMismatchError,
    EmbeddingInvalidVectorError,
    EmbeddingTextEmptyError,
)


def test_deterministic_fake_embedding_is_deterministic() -> None:
    adapter = DeterministicFakeEmbeddingAdapter(dimension=8)
    a = adapter.embed_text("hello")
    b = adapter.embed_text("hello")
    assert a == b


def test_deterministic_fake_embedding_stable_for_same_text() -> None:
    adapter = DeterministicFakeEmbeddingAdapter(dimension=8)
    v1 = adapter.embed_text("same text")
    v2 = adapter.embed_text("same text")
    assert v1 == v2
    assert len(v1) == 8


def test_embedding_service_validates_dimension() -> None:
    adapter = DeterministicFakeEmbeddingAdapter(dimension=8)
    svc = EmbeddingService(adapter=adapter, expected_dimension=7)
    with pytest.raises(EmbeddingDimensionMismatchError):
        svc.embed_text("hello")


def test_embedding_service_rejects_empty_text() -> None:
    adapter = DeterministicFakeEmbeddingAdapter(dimension=8)
    svc = EmbeddingService(adapter=adapter, expected_dimension=8)
    with pytest.raises(EmbeddingTextEmptyError):
        svc.embed_text("   ")


def test_not_configured_adapter_fails_explicitly() -> None:
    adapter = NotConfiguredEmbeddingAdapter()
    svc = EmbeddingService(adapter=adapter, expected_dimension=0)
    with pytest.raises(EmbeddingAdapterNotConfiguredError):
        svc.embed_text("hello")


def test_embedding_service_rejects_non_finite_values() -> None:
    class BadAdapter:
        dimension = 1

        def embed_text(self, text: str) -> list[float]:
            _ = text
            return [float("nan")]

    svc = EmbeddingService(adapter=BadAdapter(), expected_dimension=1)
    with pytest.raises(EmbeddingInvalidVectorError):
        svc.embed_text("hello")


def test_embedding_service_rejects_non_numeric_values() -> None:
    class BadAdapter:
        dimension = 1

        def embed_text(self, text: str):  # type: ignore[no-untyped-def]
            _ = text
            return ["nope"]

    svc = EmbeddingService(adapter=BadAdapter(), expected_dimension=1)
    with pytest.raises(EmbeddingInvalidVectorError):
        svc.embed_text("hello")

