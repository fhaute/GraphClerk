from __future__ import annotations

import uuid

import pytest

from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.errors import ExtractorNotRegisteredError, ExtractorUnavailableError
from app.services.extraction import ArtifactExtractor, ExtractorRegistry


def _dummy_artifact() -> Artifact:
    return Artifact(
        id=uuid.uuid4(),
        filename="stub.pdf",
        title=None,
        artifact_type="pdf",
        mime_type="application/pdf",
        storage_uri="test://stub",
        checksum=None,
        size_bytes=0,
        raw_text=None,
        metadata_json=None,
    )


class UnavailableStubExtractor:
    """Registered but not runnable — surfaces ExtractorUnavailableError."""

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        raise ExtractorUnavailableError("stub: multimodal extractor not runnable")


class EchoStubExtractor:
    """Minimal runnable stub for protocol checks (not used for unavailable path)."""

    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        return [
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="stub",
                text="x",
                location={},
                source_fidelity=SourceFidelity.extracted,
                confidence=1.0,
            )
        ]


def test_register_stub_get_returns_same_instance() -> None:
    reg = ExtractorRegistry()
    stub = UnavailableStubExtractor()
    reg.register(Modality.pdf, stub)
    assert reg.get(Modality.pdf) is stub


def test_unregistered_modality_raises_extractor_not_registered() -> None:
    reg = ExtractorRegistry()
    with pytest.raises(ExtractorNotRegisteredError) as ei:
        reg.get(Modality.pdf)
    assert "pdf" in str(ei.value).lower()


def test_stub_extractor_raises_extractor_unavailable() -> None:
    ext = UnavailableStubExtractor()
    with pytest.raises(ExtractorUnavailableError):
        ext.extract(_dummy_artifact())


def test_stub_conforms_to_artifact_extractor_protocol() -> None:
    stub = UnavailableStubExtractor()
    assert isinstance(stub, ArtifactExtractor)
    echo = EchoStubExtractor()
    assert isinstance(echo, ArtifactExtractor)


def test_registry_has_no_default_video_or_text_extractors() -> None:
    reg = ExtractorRegistry()
    for m in (Modality.text, Modality.video):
        with pytest.raises(ExtractorNotRegisteredError):
            reg.get(m)
