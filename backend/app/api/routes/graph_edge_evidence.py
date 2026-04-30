from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.db.session import get_sessionmaker
from app.schemas.graph_evidence_link import GraphEdgeEvidenceLinkResponse, GraphEvidenceLinkCreateRequest
from app.services.errors import (
    EvidenceUnitNotFoundError,
    GraphEdgeEvidenceLinkAlreadyExistsError,
    GraphEdgeNotFoundError,
)
from app.services.graph_edge_evidence_service import GraphEdgeEvidenceService

router = APIRouter(prefix="/graph", tags=["graph"])


def _to_response(link) -> GraphEdgeEvidenceLinkResponse:
    return GraphEdgeEvidenceLinkResponse(
        id=str(link.id),
        graph_edge_id=str(link.graph_edge_id),
        evidence_unit_id=str(link.evidence_unit_id),
        support_type=link.support_type,
        confidence=link.confidence,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.post("/edges/{edge_id}/evidence", response_model=GraphEdgeEvidenceLinkResponse)
def attach_evidence_to_graph_edge(edge_id: str, payload: GraphEvidenceLinkCreateRequest) -> GraphEdgeEvidenceLinkResponse:
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphEdgeEvidenceService(session=session)
        try:
            link = svc.attach(
                graph_edge_id=uuid.UUID(edge_id),
                evidence_unit_id=uuid.UUID(payload.evidence_unit_id),
                support_type=payload.support_type,
                confidence=payload.confidence,
            )
            session.commit()
            return _to_response(link)
        except GraphEdgeNotFoundError as e:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(e)) from e
        except EvidenceUnitNotFoundError as e:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(e)) from e
        except GraphEdgeEvidenceLinkAlreadyExistsError as e:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(e)) from e

