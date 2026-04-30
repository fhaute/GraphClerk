from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.artifact import Artifact
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate
from app.services.artifact_service import ArtifactService
from app.services.evidence_unit_service import EvidenceUnitService
from app.services.errors import IngestionParseError
from app.services.parsers.markdown_parser import MarkdownParser
from app.services.parsers.plain_text_parser import PlainTextParser
from app.services.raw_source_store import RawSourceStore


@dataclass(frozen=True)
class IngestResult:
    artifact: Artifact
    evidence_unit_count: int


class TextIngestionService:
    """Orchestrate Phase 2 ingestion for text and Markdown artifacts."""

    def __init__(self, *, settings: Settings) -> None:
        self._settings = settings

    def ingest(
        self,
        *,
        session: Session,
        filename: str,
        artifact_type: str,
        mime_type: str | None,
        content_bytes: bytes,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IngestResult:
        """Ingest a text/Markdown artifact into EvidenceUnits.

        Artifact + EvidenceUnits are created in a single transaction where practical.
        If a disk write occurs and the DB transaction fails afterwards, we attempt
        best-effort cleanup of the disk file.
        """

        raw_store = RawSourceStore(self._settings)
        artifact_service = ArtifactService(session=session, raw_source_store=raw_store)
        evidence_service = EvidenceUnitService(session=session)

        disk_path_str: str | None = None
        try:
            with session.begin():
                artifact, disk_path_str = artifact_service.create_from_bytes(
                    filename=filename,
                    artifact_type=artifact_type,
                    mime_type=mime_type,
                    content_bytes=content_bytes,
                    title=title,
                    metadata=metadata,
                )
                # Ensure Artifact has an id before creating dependent EvidenceUnits.
                session.flush()

                try:
                    text = content_bytes.decode("utf-8")
                except UnicodeDecodeError as e:
                    raise IngestionParseError("Artifact content is not valid UTF-8 text.") from e

                candidates = self._parse(artifact_type=artifact_type, text=text)
                evidence_service.create_from_candidates(artifact_id=artifact.id, candidates=candidates)

            # committed
            return IngestResult(artifact=artifact, evidence_unit_count=len(candidates))
        except Exception:
            # best-effort cleanup if disk write happened but DB failed
            if disk_path_str:
                from pathlib import Path

                raw_store.best_effort_cleanup(Path(disk_path_str))
            raise

    def _parse(self, *, artifact_type: str, text: str) -> list[EvidenceUnitCandidate]:
        try:
            if artifact_type == "markdown":
                return MarkdownParser().parse(text)
            return PlainTextParser().parse(text)
        except Exception as e:
            raise IngestionParseError(str(e)) from e

