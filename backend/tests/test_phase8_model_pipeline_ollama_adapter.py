"""Track D Slice D3 — Ollama ``/api/generate`` adapter (mocked HTTP; no live Ollama)."""

from __future__ import annotations

import ast
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError

from app.services.model_pipeline_contracts import (
    ModelOutputKind,
    ModelPipelineInputKind,
    ModelPipelineRequestEnvelope,
    ModelPipelineRole,
    ModelPipelineStatus,
    ModelPipelineTask,
)
from app.services.model_pipeline_ollama_adapter import (
    CODE_INVALID_JSON,
    CODE_OLLAMA_HTTP_ERROR,
    CODE_OLLAMA_UNAVAILABLE,
    CODE_SCHEMA_MISMATCH,
    OllamaModelPipelineAdapter,
)
from app.services.model_pipeline_output_validation_service import (
    ModelPipelineOutputValidationService,
)


def _task(**kwargs: object) -> ModelPipelineTask:
    d: dict[str, object] = {
        "role": ModelPipelineRole.evidence_candidate_enricher,
        "input_kind": ModelPipelineInputKind.extraction_context,
        "output_kind": ModelOutputKind.candidate_metadata,
        "payload": {"hint": "x"},
        "metadata": {},
    }
    d.update(kwargs)
    return ModelPipelineTask(**d)


def _envelope(**kwargs: object) -> ModelPipelineRequestEnvelope:
    d: dict[str, object] = {
        "request_id": "req-ollama-1",
        "task": _task(),
        "schema_version": "phase8.v1",
    }
    d.update(kwargs)
    return ModelPipelineRequestEnvelope(**d)


class _FakeHttpResponse:
    __slots__ = ("_body",)

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _respond(body: bytes):
    def _open(req: object, timeout: object = None, **_kw: object) -> _FakeHttpResponse:
        return _FakeHttpResponse(body)

    return _open


def test_success_maps_json_response_to_result() -> None:
    inner = {"tags": ["a"], "confidence": 0.9}
    outer = {"model": "llama3.1:8b", "response": json.dumps(inner), "done": True}
    captured: dict[str, object] = {}

    def fake_open(req: object, timeout: object = None, **_kw: object) -> _FakeHttpResponse:
        captured["timeout"] = timeout
        url = getattr(req, "full_url", None) or str(req)
        assert "api/generate" in url
        return _FakeHttpResponse(json.dumps(outer).encode("utf-8"))

    env = _envelope()
    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434/",
        model="llama3.1:8b",
        timeout_seconds=12.0,
        urlopen=fake_open,
    )
    out = adapter.run(env)
    assert captured["timeout"] == 12.0
    assert out.status == ModelPipelineStatus.success
    assert out.error is None
    assert out.result is not None
    assert out.request_id == env.request_id
    assert out.schema_version == env.schema_version
    assert out.result.role == env.task.role
    assert out.result.output_kind == env.task.output_kind
    assert out.result.payload == inner
    assert out.result.provenance["source"] == "ollama"
    assert out.result.provenance["model"] == "llama3.1:8b"
    assert out.result.provenance["adapter"] == "ollama"


def test_warnings_extracted_from_inner_json() -> None:
    inner = {"foo": 1, "warnings": ["note"]}
    outer = {"response": json.dumps(inner)}
    adapter = OllamaModelPipelineAdapter(
        base_url="http://127.0.0.1:11434",
        model="m",
        timeout_seconds=30.0,
        urlopen=_respond(json.dumps(outer).encode()),
    )
    out = adapter.run(_envelope())
    assert out.status == ModelPipelineStatus.success
    assert out.result is not None
    assert out.result.warnings == ["note"]
    assert out.result.payload == {"foo": 1}


def test_connection_error_unavailable_retryable() -> None:
    def boom(req: object, timeout: object = None, **_kw: object) -> _FakeHttpResponse:
        raise URLError("connection refused")

    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=boom,
    )
    out = adapter.run(_envelope())
    assert out.status == ModelPipelineStatus.unavailable
    assert out.error is not None
    assert out.error.code == CODE_OLLAMA_UNAVAILABLE
    assert out.error.retryable is True


def test_non_2xx_http_error() -> None:
    err = HTTPError("url", 500, "Server Error", hdrs=None, fp=BytesIO(b"error body"))

    def raise_http(req: object, timeout: object = None, **_kw: object) -> _FakeHttpResponse:
        raise err

    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=raise_http,
    )
    out = adapter.run(_envelope())
    assert out.status == ModelPipelineStatus.error
    assert out.error is not None
    assert out.error.code == CODE_OLLAMA_HTTP_ERROR
    assert out.error.retryable is False


def test_429_http_error_retryable() -> None:
    err = HTTPError("url", 429, "Too Many", hdrs=None, fp=BytesIO(b"{}"))

    def raise_http(req: object, timeout: object = None, **_kw: object) -> _FakeHttpResponse:
        raise err

    out = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=raise_http,
    ).run(_envelope())
    assert out.error is not None
    assert out.error.retryable is True
    assert out.error.code == CODE_OLLAMA_HTTP_ERROR


def test_invalid_outer_json() -> None:
    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=_respond(b"not-json{"),
    )
    out = adapter.run(_envelope())
    assert out.status == ModelPipelineStatus.error
    assert out.error and out.error.code == CODE_INVALID_JSON
    assert out.error.retryable is False


def test_outer_json_missing_response_field() -> None:
    outer = {"done": True, "model": "m"}
    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=_respond(json.dumps(outer).encode()),
    )
    out = adapter.run(_envelope())
    assert out.error and out.error.code == CODE_SCHEMA_MISMATCH


def test_response_text_not_json() -> None:
    outer = {"response": "just prose not json"}
    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=_respond(json.dumps(outer).encode()),
    )
    out = adapter.run(_envelope())
    assert out.error and out.error.code == CODE_INVALID_JSON


def test_inner_payload_truth_claim_rejected_at_result_contract() -> None:
    inner = {"is_evidence": True}
    outer = {"response": json.dumps(inner)}
    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=_respond(json.dumps(outer).encode()),
    )
    out = adapter.run(_envelope())
    assert out.status == ModelPipelineStatus.error
    assert out.error and out.error.code == CODE_SCHEMA_MISMATCH


def test_prompt_does_not_solicit_answers_or_evidence() -> None:
    adapter = OllamaModelPipelineAdapter(
        base_url="http://x",
        model="m",
        timeout_seconds=1.0,
        urlopen=MagicMock(side_effect=AssertionError("no network")),
    )
    task = _task()
    prompt = adapter._build_prompt(task)
    lower = prompt.lower()
    assert "write the final answer" not in lower
    assert "produce evidence" not in lower
    assert "verbatim source" not in lower
    assert "do not produce narrative answers" in lower
    assert "do not use key is_evidence" in lower


def test_run_does_not_mutate_request_envelope() -> None:
    inner = {"k": 1}
    outer = {"response": json.dumps(inner)}
    env = _envelope()
    payload_id_before = id(env.task.payload)
    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=_respond(json.dumps(outer).encode()),
    )
    adapter.run(env)
    assert id(env.task.payload) == payload_id_before
    assert env.task.payload == {"hint": "x"}


def test_uses_api_generate_path_in_request() -> None:
    urls: list[str] = []

    def capture(req: object, timeout: object = None, **_kw: object) -> _FakeHttpResponse:
        urls.append(getattr(req, "full_url", str(req)))
        return _FakeHttpResponse(json.dumps({"response": json.dumps({"ok": True})}).encode())

    OllamaModelPipelineAdapter(
        base_url="http://host:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=capture,
    ).run(_envelope())
    assert urls and urls[0].endswith("/api/generate")


def test_validation_service_blocks_prose_like_payload_after_adapter_success() -> None:
    inner = {"answer": "I will synthesize everything"}
    outer = {"response": json.dumps(inner)}
    adapter = OllamaModelPipelineAdapter(
        base_url="http://localhost:11434",
        model="m",
        timeout_seconds=5.0,
        urlopen=_respond(json.dumps(outer).encode()),
    )
    resp = adapter.run(_envelope())
    assert resp.status == ModelPipelineStatus.success
    assert resp.result is not None
    report = ModelPipelineOutputValidationService().validate_response(resp)
    assert report.ok is False


def test_ollama_module_imports_avoid_forbidden_services() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "app" / "services" / "model_pipeline_ollama_adapter.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {
        "app.services.file_clerk_service",
        "app.services.text_ingestion_service",
        "app.services.multimodal_ingestion_service",
        "app.services.evidence_enrichment_service",
        "app.services.retrieval_packet_builder",
        "app.services.evidence_selection_service",
        "app.services.model_pipeline_candidate_projection_service",
        "app.services.model_pipeline_output_validation_service",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert not (imported & forbidden)
