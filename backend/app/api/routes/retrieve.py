"""Phase 4 File Clerk retrieval endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db.session import get_sessionmaker
from app.schemas.retrieval_packet import RetrieveRequest, RetrievalPacket
from app.services.errors import (
    EmbeddingTextEmptyError,
    SemanticIndexSearchInconsistentIndexError,
)
from app.services.file_clerk_service import FileClerkService

router = APIRouter(prefix="", tags=["retrieve"])


@router.post("/retrieve", response_model=RetrievalPacket)
def retrieve_packet(payload: RetrieveRequest) -> RetrievalPacket:
    """Return a structured `RetrievalPacket` for a natural-language question."""

    if payload.question.strip() == "":
        raise HTTPException(status_code=422, detail="question_empty")

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        try:
            svc = FileClerkService(session=session)
            return svc.retrieve(payload.question, payload.options, actor_context=payload.actor_context)
        except EmbeddingTextEmptyError as e:
            session.rollback()
            raise HTTPException(status_code=422, detail="embedding_text_empty") from e
        except SemanticIndexSearchInconsistentIndexError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="semantic_index_search_inconsistent_index") from e
