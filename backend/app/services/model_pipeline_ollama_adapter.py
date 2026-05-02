"""Ollama HTTP adapter for Phase 8 model pipeline (Track D Slice D3).

Calls Ollama ``POST /api/generate`` (not ``/api/chat``) with ``stream: false`` and
``format: \"json\"`` so the ``response`` field contains JSON text parseable into a
payload dict for :class:`ModelPipelineResult`.

Uses stdlib :mod:`urllib` only — no extra dependencies. Downstream
:class:`ModelPipelineOutputValidationService` remains responsible for semantic bounds.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request
from urllib.request import urlopen as default_urlopen

from pydantic import ValidationError

from app.services.model_pipeline_contracts import (
    ModelPipelineError,
    ModelPipelineRequestEnvelope,
    ModelPipelineResponseEnvelope,
    ModelPipelineResult,
    ModelPipelineStatus,
    ModelPipelineTask,
)

# Stable codes for operator/tests (align with Track D decision doc).
CODE_OLLAMA_UNAVAILABLE = "model_pipeline_ollama_unavailable"
CODE_OLLAMA_HTTP_ERROR = "model_pipeline_ollama_http_error"
CODE_INVALID_JSON = "model_pipeline_invalid_json"
CODE_SCHEMA_MISMATCH = "model_pipeline_schema_mismatch"


class OllamaModelPipelineAdapter:
    """HTTP client for Ollama ``/api/generate`` wired to :class:`ModelPipelineAdapter`."""

    __slots__ = ("_base_url", "_model", "_timeout_seconds", "_urlopen")

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        urlopen: Callable[..., Any] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._urlopen = urlopen if urlopen is not None else default_urlopen

    def _generate_url(self) -> str:
        return f"{self._base_url}/api/generate"

    def _failure(
        self,
        envelope: ModelPipelineRequestEnvelope,
        *,
        status: ModelPipelineStatus,
        code: str,
        message: str,
        retryable: bool,
        details: dict[str, Any] | None = None,
    ) -> ModelPipelineResponseEnvelope:
        err = ModelPipelineError(
            code=code,
            message=message,
            retryable=retryable,
            details=details or {},
        )
        return ModelPipelineResponseEnvelope(
            request_id=envelope.request_id,
            status=status,
            result=None,
            error=err,
            warnings=[code],
            metadata={"pipeline_adapter": "ollama"},
            schema_version=envelope.schema_version,
        )

    def _build_prompt(self, task: ModelPipelineTask) -> str:
        """Structured prompt: metadata-only JSON contract; no answer/evidence synthesis."""

        payload_json = json.dumps(task.payload, sort_keys=True)
        meta_json = json.dumps(task.metadata, sort_keys=True)
        lines = [
            "You assist GraphClerk with structured helper metadata only.",
            "",
            f"task_role: {task.role.value}",
            f"input_kind: {task.input_kind.value}",
            f"output_kind: {task.output_kind.value}",
            "",
            f"task_payload_json: {payload_json}",
            f"task_metadata_json: {meta_json}",
            "",
            "Return a single JSON object only (no markdown code fences, no prose outside JSON).",
            "The object becomes helper metadata for the given output_kind — not evidence.",
            "",
            "Hard constraints on your JSON object:",
            "- Do not use key is_evidence or set source_fidelity to verbatim.",
            "- Do not use keys: source_truth, answer, final_answer, citations.",
            "- Do not produce narrative answers, evidence passages, or retrieval routing.",
            "",
            'Optional top-level key "warnings": array of short strings.',
            "",
            "Return valid JSON only.",
        ]
        return "\n".join(lines)

    def run(self, envelope: ModelPipelineRequestEnvelope) -> ModelPipelineResponseEnvelope:
        """POST ``/api/generate``; parse ``response`` JSON into :class:`ModelPipelineResult`."""

        prompt = self._build_prompt(envelope.task)
        body_obj: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        raw = json.dumps(body_obj).encode("utf-8")
        req = Request(
            self._generate_url(),
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self._urlopen(req, timeout=self._timeout_seconds) as resp:
                resp_bytes = resp.read()
        except HTTPError as e:
            retryable = e.code in (429, 503)
            snippet = ""
            try:
                snippet = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            details: dict[str, Any] = {"http_status": e.code}
            if snippet:
                details["body_snippet"] = snippet
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_OLLAMA_HTTP_ERROR,
                message=f"Ollama HTTP error (status {e.code}).",
                retryable=retryable,
                details=details,
            )
        except (URLError, TimeoutError, OSError) as e:
            return self._failure(
                envelope,
                status=ModelPipelineStatus.unavailable,
                code=CODE_OLLAMA_UNAVAILABLE,
                message=f"Ollama request failed: {e}",
                retryable=True,
                details={"reason": type(e).__name__},
            )

        try:
            outer = json.loads(resp_bytes.decode("utf-8"))
        except json.JSONDecodeError as e:
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_INVALID_JSON,
                message="Ollama response body is not valid JSON.",
                retryable=False,
                details={"reason": str(e)},
            )

        if not isinstance(outer, dict):
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_SCHEMA_MISMATCH,
                message="Ollama JSON root must be an object.",
                retryable=False,
                details={},
            )

        if "response" not in outer:
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_SCHEMA_MISMATCH,
                message="Ollama JSON missing required field 'response'.",
                retryable=False,
                details={},
            )

        response_text = outer["response"]
        if not isinstance(response_text, str):
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_SCHEMA_MISMATCH,
                message="Ollama field 'response' must be a string.",
                retryable=False,
                details={},
            )

        try:
            inner = json.loads(response_text)
        except json.JSONDecodeError as e:
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_INVALID_JSON,
                message="Ollama 'response' text is not valid JSON.",
                retryable=False,
                details={"reason": str(e)},
            )

        if not isinstance(inner, dict):
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_SCHEMA_MISMATCH,
                message="Parsed model JSON must be an object.",
                retryable=False,
                details={},
            )

        inner_work = dict(inner)
        raw_w = inner_work.pop("warnings", None)
        warnings: list[str] = []
        if isinstance(raw_w, list) and all(isinstance(x, str) for x in raw_w):
            warnings = list(raw_w)

        provenance: dict[str, Any] = {
            "source": "ollama",
            "model": self._model,
            "adapter": "ollama",
        }

        try:
            result = ModelPipelineResult(
                role=envelope.task.role,
                output_kind=envelope.task.output_kind,
                status=ModelPipelineStatus.success,
                payload=inner_work,
                warnings=warnings,
                provenance=provenance,
            )
        except ValidationError as e:
            return self._failure(
                envelope,
                status=ModelPipelineStatus.error,
                code=CODE_SCHEMA_MISMATCH,
                message="Model JSON does not satisfy ModelPipelineResult contract.",
                retryable=False,
                details={"validation_errors": e.errors()},
            )

        return ModelPipelineResponseEnvelope(
            request_id=envelope.request_id,
            status=ModelPipelineStatus.success,
            result=result,
            error=None,
            warnings=warnings,
            metadata={"pipeline_adapter": "ollama"},
            schema_version=envelope.schema_version,
        )


__all__ = [
    "CODE_INVALID_JSON",
    "CODE_OLLAMA_HTTP_ERROR",
    "CODE_OLLAMA_UNAVAILABLE",
    "CODE_SCHEMA_MISMATCH",
    "OllamaModelPipelineAdapter",
]