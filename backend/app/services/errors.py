from __future__ import annotations


class GraphClerkError(Exception):
    """Base error type for explicit GraphClerk failures."""


class UnsupportedArtifactTypeError(GraphClerkError):
    """Raised when an artifact type is not supported in the current phase."""


class ExtractorNotRegisteredError(GraphClerkError):
    """Raised when no multimodal extractor is registered for the modality."""


class ExtractorUnavailableError(GraphClerkError):
    """Raised when a registered extractor cannot run (e.g. missing optional dependency)."""


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


class VectorIndexUnavailableError(GraphClerkError):
    """Raised when the vector index (Qdrant) is unreachable or misconfigured."""


class VectorIndexDimensionMismatchError(GraphClerkError):
    """Raised when a vector does not match the expected dimension."""


class VectorIndexOperationError(GraphClerkError):
    """Raised when a Qdrant operation fails unexpectedly."""


class SemanticIndexSearchInconsistentIndexError(GraphClerkError):
    """Raised when Qdrant results cannot be reconciled with Postgres source of truth."""


class QueryIntentError(GraphClerkError):
    """Raised when query intent classification fails unexpectedly."""


class SemanticIndexResolutionError(GraphClerkError):
    """Raised when a semantic index cannot be resolved for traversal."""


class GraphTraversalError(GraphClerkError):
    """Raised when graph traversal fails unexpectedly."""


class EvidenceSelectionError(GraphClerkError):
    """Raised when evidence selection fails unexpectedly."""


class ContextBudgetError(GraphClerkError):
    """Raised when context budgeting fails unexpectedly."""


class RetrievalPacketBuildError(GraphClerkError):
    """Raised when a RetrievalPacket cannot be assembled or validated."""


class InvalidSourceFidelityError(GraphClerkError):
    """Raised when source_fidelity is not a permitted SourceFidelity value."""


class InvalidEvidenceUnitCandidateError(GraphClerkError):
    """Raised when an EvidenceUnitCandidate fails structural validation (e.g. empty text)."""

