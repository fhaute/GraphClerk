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


class GraphNodeNotFoundError(GraphClerkError):
    """Raised when a graph node is not found."""


class GraphEdgeNotFoundError(GraphClerkError):
    """Raised when a graph edge is not found."""


class InvalidRelationTypeError(GraphClerkError):
    """Raised when a graph edge relation_type is invalid."""


class GraphNodeEvidenceLinkAlreadyExistsError(GraphClerkError):
    """Raised when a GraphNodeEvidence link already exists."""


class GraphEdgeEvidenceLinkAlreadyExistsError(GraphClerkError):
    """Raised when a GraphEdgeEvidence link already exists."""


class SemanticIndexNotFoundError(GraphClerkError):
    """Raised when a semantic index is not found."""


class SemanticIndexRequiresEntryNodesError(GraphClerkError):
    """Raised when a semantic index creation request has no entry nodes."""


class DuplicateEntryNodeIdError(GraphClerkError):
    """Raised when a semantic index creation request has duplicate entry node IDs."""


class EmbeddingAdapterNotConfiguredError(GraphClerkError):
    """Raised when no embedding adapter is configured."""


class EmbeddingTextEmptyError(GraphClerkError):
    """Raised when embedding text is empty or whitespace-only."""


class EmbeddingInvalidVectorError(GraphClerkError):
    """Raised when an adapter returns a non-numeric or non-finite vector."""


class EmbeddingDimensionMismatchError(GraphClerkError):
    """Raised when an adapter returns a vector of unexpected dimension."""


class EmbeddingGenerationError(GraphClerkError):
    """Raised when embedding generation fails explicitly."""

