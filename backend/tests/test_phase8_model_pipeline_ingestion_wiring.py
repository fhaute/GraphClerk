"""Track D Slice D6 — model metadata enrichment wired into ``POST /artifacts`` ingestion."""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
import pytest
from httpx import ASGITransport
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.routes import artifacts as artifacts_routes
from app.core import config as config_module
from app.core.config import Settings
from app.main import create_app
from app.models.artifact import Artifact
from app.models.enums import Modality, SourceFidelity
from app.models.evidence_unit import EvidenceUnit
from app.schemas.evidence_unit_candidate import (
    LANGUAGE_METADATA_KEY_LANGUAGE,
    EvidenceUnitCandidate,
)
from app.services.artifact_language_aggregation_service import GRAPHCLERK_LANGUAGE_AGGREGATION_KEY
from app.services.evidence_enrichment_service import EvidenceEnrichmentService
from app.services.language_detection_service import (
    DeterministicTestLanguageDetectionAdapter,
    LanguageDetectionService,
)
from app.services.model_pipeline_candidate_projection_service import (
    GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY,
    ModelPipelineCandidateMetadataProjectionService,
)
from app.services.model_pipeline_contracts import (
    DeterministicTestModelPipelineAdapter,
    ModelPipelineRequestEnvelope,
    ModelPipelineResult,
    ModelPipelineRole,
    ModelPipelineStatus,
    NotConfiguredModelPipelineAdapter,
)
from app.services.model_pipeline_metadata_enrichment_service import (
    ModelPipelineMetadataEnrichmentService,
)
from app.services.model_pipeline_output_validation_service import (
    ModelPipelineOutputValidationService,
)
from app.services.model_pipeline_purpose_registry import (
    ModelPipelinePurposeConfig,
    ModelPipelinePurposeRegistry,
    ModelPipelinePurposeResolution,
    build_default_model_pipeline_purpose_registry,
    resolve_model_pipeline_purpose,
)


def _session() -> Session:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return Session(engine, expire_on_commit=False)


def _base_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@localhost:5432/db",
    )
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")
    monkeypatch.delenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", raising=False)
    monkeypatch.delenv("GRAPHCLERK_SEMANTIC_SEARCH_EMBEDDING_ADAPTER", raising=False)
    for key in (
        "GRAPHCLERK_MODEL_PIPELINE_ADAPTER",
        "GRAPHCLERK_MODEL_PIPELINE_BASE_URL",
        "GRAPHCLERK_MODEL_PIPELINE_MODEL",
        "GRAPHCLERK_MODEL_PIPELINE_TIMEOUT_SECONDS",
        "GRAPHCLERK_MODEL_PIPELINE_API_KEY",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL",
        "GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)


def _fake_deterministic_adapter_factory() -> Any:
    def _factory(envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResult:
        return ModelPipelineResult(
            role=envelope.task.role,
            output_kind=envelope.task.output_kind,
            status=ModelPipelineStatus.success,
            payload={"labels": ["d6-ingest"], "hints": ["track-d"]},
            warnings=[],
            provenance={"source": "deterministic_test", "run": envelope.request_id},
        )

    return DeterministicTestModelPipelineAdapter(factory=_factory)


@pytest.fixture(autouse=True)
def _clear_pipeline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_app_env(monkeypatch)
    config_module.get_settings.cache_clear()
    yield
    _base_app_env(monkeypatch)
    config_module.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_default_post_artifacts_no_graphclerk_model_pipeline(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _base_app_env(monkeypatch)
    config_module.get_settings.cache_clear()

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "d6-default.txt",
                "artifact_type": "text",
                "text": "Alpha paragraph.\n\nBeta paragraph.\n",
            },
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        evs = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid))
            .scalars()
            .all()
        )
    assert len(evs) >= 1
    for eu in evs:
        meta = eu.metadata_json or {}
        assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY not in meta


@pytest.mark.asyncio
async def test_enabled_enricher_persists_graphclerk_model_pipeline(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _base_app_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "purpose-model-d6")
    config_module.get_settings.cache_clear()

    monkeypatch.setattr(
        artifacts_routes,
        "build_evidence_enricher_model_pipeline_adapter",
        lambda _s, _r: _fake_deterministic_adapter_factory(),
    )

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "d6-enriched.txt",
                "artifact_type": "text",
                "text": "One block.\n\nTwo block.\n",
            },
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        evs = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid))
            .scalars()
            .all()
        )
    assert len(evs) >= 1
    for eu in evs:
        meta = eu.metadata_json or {}
        inner = meta.get(GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY)
        assert isinstance(inner, dict)
        assert inner.get("proposed", {}).get("labels") == ["d6-ingest"]
        assert eu.text  # unchanged non-empty


@pytest.mark.asyncio
async def test_language_and_model_metadata_coexist(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _base_app_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_LANGUAGE_DETECTION_ADAPTER", "lingua")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "purpose-coexist")
    config_module.get_settings.cache_clear()

    fake_ld = LanguageDetectionService(
        adapter=DeterministicTestLanguageDetectionAdapter(
            default_language="eo",
            default_confidence=0.91,
            short_text_max_chars=0,
        ),
    )
    monkeypatch.setattr(artifacts_routes, "build_language_detection_service", lambda _s: fake_ld)
    monkeypatch.setattr(
        artifacts_routes,
        "build_evidence_enricher_model_pipeline_adapter",
        lambda _s, _r: _fake_deterministic_adapter_factory(),
    )

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "d6-lang-model.txt",
                "artifact_type": "text",
                "text": "First paragraph here.\n\nSecond paragraph here.\n",
            },
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        evs = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid))
            .scalars()
            .all()
        )
        art = session.get(Artifact, aid)
    assert art is not None
    agg = (art.metadata_json or {}).get(GRAPHCLERK_LANGUAGE_AGGREGATION_KEY)
    assert isinstance(agg, dict)
    assert agg.get("primary_language") == "eo"

    for eu in evs:
        meta = eu.metadata_json or {}
        assert meta.get(LANGUAGE_METADATA_KEY_LANGUAGE) == "eo"
        assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY in meta


@pytest.mark.asyncio
async def test_runtime_adapter_non_success_does_not_fail_ingestion_or_merge_metadata(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _base_app_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "purpose-nc")
    config_module.get_settings.cache_clear()

    monkeypatch.setattr(
        artifacts_routes,
        "build_evidence_enricher_model_pipeline_adapter",
        lambda _s, _r: NotConfiguredModelPipelineAdapter(),
    )

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "d6-nc.txt",
                "artifact_type": "text",
                "text": "Only paragraph.\n",
            },
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        evs = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid))
            .scalars()
            .all()
        )
    assert len(evs) >= 1
    for eu in evs:
        meta = eu.metadata_json or {}
        assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY not in meta


@pytest.mark.asyncio
async def test_validation_failure_does_not_merge_metadata(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _base_app_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "purpose-bad")
    config_module.get_settings.cache_clear()

    def _bad(envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResult:
        return ModelPipelineResult(
            role=envelope.task.role,
            output_kind=envelope.task.output_kind,
            status=ModelPipelineStatus.success,
            payload={"nested": {"is_evidence": True}},
            warnings=[],
            provenance={"source": "deterministic_test", "run": envelope.request_id},
        )

    monkeypatch.setattr(
        artifacts_routes,
        "build_evidence_enricher_model_pipeline_adapter",
        lambda _s, _r: DeterministicTestModelPipelineAdapter(factory=_bad),
    )

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            json={
                "filename": "d6-badval.txt",
                "artifact_type": "text",
                "text": "Single paragraph block here.\n",
            },
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        ev = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid))
            .scalars()
            .first()
        )
    assert ev is not None
    assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY not in (ev.metadata_json or {})


class _PdfStubExtractor:
    def extract(self, artifact: Artifact) -> list[EvidenceUnitCandidate]:
        _ = artifact
        return [
            EvidenceUnitCandidate(
                modality=Modality.pdf,
                content_type="stub_unit",
                text="pdf stub body long enough for tests",
                location={"page": 1},
                source_fidelity=SourceFidelity.extracted,
                confidence=1.0,
            )
        ]


@pytest.mark.asyncio
async def test_multimodal_pdf_gets_same_model_enrichment_composition(
    db_ready: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.extraction import ExtractorRegistry

    _base_app_env(monkeypatch)
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "purpose-pdf")
    config_module.get_settings.cache_clear()

    reg = ExtractorRegistry()
    reg.register(Modality.pdf, _PdfStubExtractor())
    monkeypatch.setattr(artifacts_routes, "get_multimodal_extractor_registry", lambda: reg)
    monkeypatch.setattr(
        artifacts_routes,
        "build_evidence_enricher_model_pipeline_adapter",
        lambda _s, _r: _fake_deterministic_adapter_factory(),
    )

    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/artifacts",
            files={"file": ("stub.pdf", b"%PDF-1.4 stub", "application/pdf")},
        )
    assert res.status_code == 200
    aid = uuid.UUID(res.json()["artifact_id"])
    with _session() as session:
        ev = (
            session.execute(select(EvidenceUnit).where(EvidenceUnit.artifact_id == aid))
            .scalars()
            .first()
        )
    assert ev is not None
    assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY in (ev.metadata_json or {})
    assert ev.text == "pdf stub body long enough for tests"
    assert ev.source_fidelity == SourceFidelity.extracted


def test_evidence_enrichment_service_model_after_language_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct composition: language step then model step without HTTP."""

    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")

    settings = Settings()
    base_reg = build_default_model_pipeline_purpose_registry(settings)
    ec = ModelPipelineRole.evidence_candidate_enricher
    merged = dict(base_reg.configs)
    merged[ec] = ModelPipelinePurposeConfig(
        enabled=True,
        adapter="ollama",
        model="unit-model",
        timeout_seconds=12.0,
        output_kind=base_reg.configs[ec].output_kind,
    )
    reg_manual = ModelPipelinePurposeRegistry(configs=merged)
    resolution = resolve_model_pipeline_purpose(reg_manual, ec, settings)
    assert resolution.disabled is False

    mp = ModelPipelineMetadataEnrichmentService(
        adapter=_fake_deterministic_adapter_factory(),
        output_validator=ModelPipelineOutputValidationService(),
        projection_service=ModelPipelineCandidateMetadataProjectionService(),
    )
    ld = LanguageDetectionService(
        adapter=DeterministicTestLanguageDetectionAdapter(
            default_language="fr",
            default_confidence=0.88,
            short_text_max_chars=0,
        ),
    )
    svc = EvidenceEnrichmentService(
        language_detection=ld,
        model_pipeline_enrichment=mp,
        model_pipeline_enrichment_resolution=resolution,
    )
    c = EvidenceUnitCandidate(
        modality=Modality.text,
        content_type="text/plain",
        text="Enough characters for detection rules here.",
        location={},
        source_fidelity=SourceFidelity.verbatim,
        confidence=1.0,
        metadata=None,
    )
    out = svc.enrich([c])[0]
    assert out.metadata is not None
    assert out.metadata[LANGUAGE_METADATA_KEY_LANGUAGE] == "fr"
    assert GRAPHCLERK_MODEL_PIPELINE_METADATA_KEY in out.metadata
    assert out.text == c.text
    assert out.source_fidelity == c.source_fidelity


def test_build_default_registry_enables_enricher_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "ollama")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "from-settings")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_TIMEOUT_SECONDS", "42")

    settings = Settings()
    reg = build_default_model_pipeline_purpose_registry(settings)
    ec = ModelPipelineRole.evidence_candidate_enricher
    assert reg.configs[ec].enabled is True
    assert reg.configs[ec].model == "from-settings"
    assert reg.configs[ec].timeout_seconds == 42.0

    res = resolve_model_pipeline_purpose(reg, ec, settings)
    assert res.disabled is False
    assert res.model == "from-settings"
    assert res.timeout_seconds == 42.0


def test_wrong_adapter_with_enricher_enabled_raises_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_ADAPTER", "not_configured")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_ENABLED", "true")
    monkeypatch.setenv("GRAPHCLERK_MODEL_PIPELINE_EVIDENCE_ENRICHER_MODEL", "m")

    with pytest.raises(ValidationError):
        Settings()


def test_enricher_resolution_build_helper_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolution object matches expectations for disabled vs manual registry."""

    monkeypatch.setenv("APP_NAME", "GraphClerk")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "optional")

    settings = Settings()
    reg_off = build_default_model_pipeline_purpose_registry(settings)
    res_off = resolve_model_pipeline_purpose(
        reg_off,
        ModelPipelineRole.evidence_candidate_enricher,
        settings,
    )
    assert isinstance(res_off, ModelPipelinePurposeResolution)
    assert res_off.disabled is True
