from __future__ import annotations


class GraphClerkError(Exception):
    """Base error type for explicit GraphClerk failures."""


class UnsupportedArtifactTypeError(GraphClerkError):
    """Raised when an artifact type is not supported in the current phase."""


class IngestionParseError(GraphClerkError):
    """Raised when parsing fails and ingestion cannot proceed."""


class RawSourceStorageError(GraphClerkError):
    """Raised when raw source persistence fails."""


class ArtifactNotFoundError(GraphClerkError):
    """Raised when an artifact is not found."""


class EvidenceUnitNotFoundError(GraphClerkError):
    """Raised when an evidence unit is not found."""

