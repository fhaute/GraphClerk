from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db.session import get_sessionmaker
from app.repositories.evidence_unit_repository import EvidenceUnitRepository
from app.schemas.evidence_unit import EvidenceUnitListResponse, EvidenceUnitResponse

router = APIRouter(prefix="", tags=["evidence"])


def _uuid(value: str):
    import uuid

    return uuid.UUID(value)


def _ev_to_response(e) -> EvidenceUnitResponse:
    return EvidenceUnitResponse(
        id=str(e.id),
        artifact_id=str(e.artifact_id),
        modality=str(e.modality),
        content_type=e.content_type,
        text=e.text,
        location=e.location,
        source_fidelity=str(e.source_fidelity),
        confidence=e.confidence,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.get("/artifacts/{artifact_id}/evidence", response_model=EvidenceUnitListResponse)
def list_artifact_evidence(artifact_id: str, limit: int = 1000, offset: int = 0) -> EvidenceUnitListResponse:
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        repo = EvidenceUnitRepository(session)
        items = repo.list_by_artifact(_uuid(artifact_id), limit=limit, offset=offset)
        return EvidenceUnitListResponse(items=[_ev_to_response(e) for e in items])


@router.get("/evidence-units/{evidence_unit_id}", response_model=EvidenceUnitResponse)
def get_evidence_unit(evidence_unit_id: str) -> EvidenceUnitResponse:
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        repo = EvidenceUnitRepository(session)
        e = repo.get(_uuid(evidence_unit_id))
        if e is None:
            raise HTTPException(status_code=404, detail="EvidenceUnit not found.")
        return _ev_to_response(e)

