from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from app.core.constants import RAW_TEXT_DB_THRESHOLD_BYTES
from app.core.config import Settings


@dataclass(frozen=True)
class RawSourceResult:
    """Result of persisting raw source content for an Artifact."""

    checksum_sha256: str
    size_bytes: int
    storage_uri: str
    raw_text: str | None
    disk_path: Path | None


class RawSourceStore:
    """Hybrid raw-source persistence.

    - Small UTF-8 text can be stored in DB (`raw_text`) for traceability.
    - Larger sources are stored on disk under `ARTIFACTS_DIR`.
    - Storage URIs are deterministic and checksum-based.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def persist(self, *, filename: str, content_bytes: bytes) -> RawSourceResult:
        """Persist raw source bytes and return pointers/metadata.

        Raises:
            OSError: if disk writes fail when required.
        """

        checksum = hashlib.sha256(content_bytes).hexdigest()
        size_bytes = len(content_bytes)

        ext = Path(filename).suffix.lower()
        if not ext:
            ext = ".txt"

        if size_bytes <= RAW_TEXT_DB_THRESHOLD_BYTES:
            raw_text = self._try_decode_utf8(content_bytes)
            storage_uri = f"localdb://artifacts/sha256/{checksum}{ext}"
            return RawSourceResult(
                checksum_sha256=checksum,
                size_bytes=size_bytes,
                storage_uri=storage_uri,
                raw_text=raw_text,
                disk_path=None,
            )

        disk_path = self._write_to_disk(checksum=checksum, ext=ext, content_bytes=content_bytes)
        storage_uri = f"local://artifacts/sha256/{checksum[:2]}/{checksum}{ext}"
        return RawSourceResult(
            checksum_sha256=checksum,
            size_bytes=size_bytes,
            storage_uri=storage_uri,
            raw_text=None,
            disk_path=disk_path,
        )

    def best_effort_cleanup(self, disk_path: Path | None) -> None:
        """Attempt to remove a previously written disk file.

        This is used when disk write succeeded but DB transaction later fails.
        """

        if disk_path is None:
            return
        try:
            disk_path.unlink(missing_ok=True)
        except Exception:
            # Best-effort cleanup only; remaining edge-case is documented in Phase 2 tech debt.
            return

    def _write_to_disk(self, *, checksum: str, ext: str, content_bytes: bytes) -> Path:
        root = Path(self._settings.artifacts_dir)
        target_dir = root / "sha256" / checksum[:2]
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / f"{checksum}{ext}"

        # Deterministic path: if it already exists, keep it (checksum match implies same content).
        if target_path.exists():
            return target_path

        tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        with open(tmp_path, "wb") as f:
            f.write(content_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target_path)

        return target_path

    @staticmethod
    def _try_decode_utf8(content_bytes: bytes) -> str | None:
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return None

