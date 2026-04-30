from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.db.session import get_sessionmaker
from app.schemas.graph_evidence_link import GraphEvidenceLinkCreateRequest, GraphNodeEvidenceLinkResponse
from app.services.errors import (
    EvidenceUnitNotFoundError,
    GraphNodeEvidenceLinkAlreadyExistsError,
    GraphNodeNotFoundError,
)
from app.services.graph_node_evidence_service import GraphNodeEvidenceService

router = APIRouter(prefix="/graph", tags=["graph"])


def _to_response(link) -> GraphNodeEvidenceLinkResponse:
    return GraphNodeEvidenceLinkResponse(
        id=str(link.id),
        graph_node_id=str(link.graph_node_id),
        evidence_unit_id=str(link.evidence_unit_id),
        support_type=link.support_type,
        confidence=link.confidence,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.post("/nodes/{node_id}/evidence", response_model=GraphNodeEvidenceLinkResponse)
def attach_evidence_to_graph_node(node_id: str, payload: GraphEvidenceLinkCreateRequest) -> GraphNodeEvidenceLinkResponse:
    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = GraphNodeEvidenceService(session=session)
        try:
            link = svc.attach(
                graph_node_id=uuid.UUID(node_id),
                evidence_unit_id=uuid.UUID(payload.evidence_unit_id),
                support_type=payload.support_type,
                confidence=payload.confidence,
            )
            session.commit()
            return _to_response(link)
        except GraphNodeNotFoundError as e:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(e)) from e
        except EvidenceUnitNotFoundError as e:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(e)) from e
        except GraphNodeEvidenceLinkAlreadyExistsError as e:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(e)) from e

