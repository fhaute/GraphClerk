from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.artifact import Artifact
from app.repositories.artifact_repository import ArtifactRepository
from app.services.errors import RawSourceStorageError, UnsupportedArtifactTypeError
from app.services.raw_source_store import RawSourceStore


class ArtifactService:
    """Create and retrieve Artifacts for Phase 2 (text/markdown only)."""

    def __init__(self, *, session: Session, raw_source_store: RawSourceStore) -> None:
        self._session = session
        self._repo = ArtifactRepository(session)
        self._raw_source_store = raw_source_store

    def create_from_bytes(
        self,
        *,
        filename: str,
        artifact_type: str,
        mime_type: str | None,
        content_bytes: bytes,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Artifact, str | None]:
        """Create an Artifact and persist its raw source.

        Returns:
            (artifact, disk_path_str_or_none)
        """

        if artifact_type not in {"text", "markdown"}:
            raise UnsupportedArtifactTypeError(f"Unsupported artifact_type: {artifact_type!r}")

        try:
            raw = self._raw_source_store.persist(filename=filename, content_bytes=content_bytes)
        except OSError as e:
            raise RawSourceStorageError(str(e)) from e

        artifact = Artifact(
            filename=filename,
            title=title,
            artifact_type=artifact_type,
            mime_type=mime_type,
            storage_uri=raw.storage_uri,
            checksum=raw.checksum_sha256,
            size_bytes=raw.size_bytes,
            raw_text=raw.raw_text,
            metadata_json=metadata,
        )
        self._repo.add(artifact)

        return artifact, str(raw.disk_path) if raw.disk_path else None

