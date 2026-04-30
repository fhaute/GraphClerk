from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.config import Settings, get_settings

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


@dataclass(frozen=True)
class QdrantAvailability:
    """Result of a Qdrant availability check."""

    ok: bool
    detail: str | None = None


class QdrantService:
    """Minimal Qdrant service (Phase 1: connectivity only)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def _client(self) -> QdrantClient:
        # Lazy import so basic tooling/tests can run before deps are installed.
        from qdrant_client import QdrantClient

        return QdrantClient(url=self._settings.qdrant_url, api_key=self._settings.qdrant_api_key)

    def check_available(self) -> QdrantAvailability:
        """Verify Qdrant is reachable with a real API call."""

        try:
            client = self._client()
            client.get_collections()
            return QdrantAvailability(ok=True)
        except Exception as e:  # noqa: BLE001 - surfaced explicitly in detail
            return QdrantAvailability(ok=False, detail=str(e))

