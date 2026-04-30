"""Phase 6 Slice A — read-only RetrievalLog APIs."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.db.session import get_sessionmaker
from app.repositories.retrieval_log_repository import RetrievalLogRepository
from app.schemas.retrieval_log import (
    RetrievalLogDetailResponse,
    RetrievalLogListResponse,
    RetrievalLogSummary,
)

router = APIRouter(prefix="", tags=["retrieval_logs"])

_MAX_LIST_LIMIT = 100


def _log_to_summary(row) -> RetrievalLogSummary:
    eu_ids = row.evidence_unit_ids or []
    return RetrievalLogSummary(
        id=str(row.id),
        question=row.question,
        confidence=row.confidence,
        warnings=list(row.warnings) if row.warnings is not None else None,
        latency_ms=row.latency_ms,
        token_estimate=row.token_estimate,
        evidence_unit_count=len(eu_ids),
        has_retrieval_packet=row.retrieval_packet is not None,
        created_at=row.created_at,
    )


def _log_to_detail(row) -> RetrievalLogDetailResponse:
    sel = row.selected_indexes
    selected_list: list[dict[str, Any]] | None = None
    if sel is not None:
        selected_list = list(sel)

    return RetrievalLogDetailResponse(
        id=str(row.id),
        question=row.question,
        selected_indexes=selected_list,
        graph_path=row.graph_path,
        evidence_unit_ids=(
            list(row.evidence_unit_ids) if row.evidence_unit_ids is not None else None
        ),
        confidence=row.confidence,
        warnings=list(row.warnings) if row.warnings is not None else None,
        latency_ms=row.latency_ms,
        token_estimate=row.token_estimate,
        metadata=row.metadata_json,
        retrieval_packet=row.retrieval_packet,
        created_at=row.created_at,
    )


@router.get("/retrieval-logs", response_model=RetrievalLogListResponse)
def list_retrieval_logs(
    limit: int = Query(default=50, ge=1, le=_MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> RetrievalLogListResponse:
    """List retrieval logs newest-first (summary fields only)."""

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        repo = RetrievalLogRepository(session)
        rows = repo.list_recent(limit=limit, offset=offset)
        return RetrievalLogListResponse(items=[_log_to_summary(r) for r in rows])


@router.get("/retrieval-logs/{retrieval_log_id}", response_model=RetrievalLogDetailResponse)
def get_retrieval_log(retrieval_log_id: str) -> RetrievalLogDetailResponse:
    """Return one retrieval log including `retrieval_packet` when present."""

    try:
        lid = uuid.UUID(retrieval_log_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail="invalid_retrieval_log_id") from e

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        repo = RetrievalLogRepository(session)
        row = repo.get(lid)
        if row is None:
            raise HTTPException(status_code=404, detail="RetrievalLog not found.")
        return _log_to_detail(row)
