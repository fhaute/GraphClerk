"""RetrievalPacket JSON contracts: Phase 4 File Clerk plus Phase 7 context extensions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.retrieval import ActorContext

PacketType = Literal["retrieval_packet"]

ActorContextInfluence = Literal["none", "recorded_only_no_route_boost_applied"]

IntentType = Literal["explain", "compare", "locate", "summarize", "debug", "recommend", "unknown"]

AnswerMode = Literal[
    "answer_with_evidence",
    "answer_with_caveats",
    "ask_clarification",
    "not_enough_evidence",
    "conflicting_evidence",
    "unsupported",
]

class InterpretedIntent(BaseModel):
    """Deterministic query intent classification output."""

    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


class SelectedSemanticIndex(BaseModel):
    """A semantic index chosen for graph entry and traversal."""

    semantic_index_id: str
    meaning: str
    score: float
    selection_reason: str


class GraphPathPacket(BaseModel):
    """Bounded traversal snapshot attached to the packet."""

    start_node_id: str
    nodes: list[str]
    edges: list[str]
    depth: int


class EvidenceUnitPacket(BaseModel):
    """Evidence grounded via graph support links, included in the packet."""

    evidence_unit_id: str
    artifact_id: str
    modality: str
    content_type: str
    source_fidelity: str
    text: str | None = None
    location: dict[str, Any] | None = None
    selection_reason: str
    confidence: float | None = None


class EvidenceLanguageAggregateRow(BaseModel):
    """Per-language rollups over selected evidence metadata (Phase 7)."""

    language: str
    evidence_unit_count: int
    average_confidence: float | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None


class RetrievalLanguageContext(BaseModel):
    """Language routing metadata derived from selected evidence ``metadata_json`` only.

    Not source truth; no detection or translation in Phase 7 Slice 7F.
    """

    version: Literal[1] = 1
    source: Literal["selected_evidence_metadata"] = "selected_evidence_metadata"
    query_language: str | None = None
    evidence_languages: list[EvidenceLanguageAggregateRow] = Field(default_factory=list)
    primary_evidence_language: str | None = None
    distinct_evidence_language_count: int = 0
    evidence_units_without_language_metadata_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class AlternativeInterpretation(BaseModel):
    """Explicit ambiguity / alternate meaning routing hints."""

    if_user_meant: str
    suggested_semantic_indexes: list[str]
    reason: str


class ContextBudgetSummary(BaseModel):
    """Visible context budgeting decisions."""

    max_evidence_units: int
    selected_evidence_units: int
    pruned_evidence_units: int
    pruning_reasons: list[str]
    max_graph_paths: int | None = None
    max_selected_indexes: int | None = None


class RetrieveOptions(BaseModel):
    """Optional tuning for a single retrieval request."""

    max_evidence_units: int = Field(default=8, ge=1, le=64)
    max_graph_depth: int = Field(default=1, ge=0, le=5)
    max_graph_paths: int = Field(default=3, ge=1, le=32)
    max_selected_indexes: int = Field(default=3, ge=1, le=16)
    include_alternatives: bool = True
    max_tokens_estimate: int | None = Field(default=None, ge=1, le=100_000)


class RetrieveRequest(BaseModel):
    """HTTP body for `POST /retrieve`."""

    question: str
    options: RetrieveOptions | None = None
    actor_context: ActorContext | None = None


class PacketActorContextRecording(BaseModel):
    """How request ``ActorContext`` was reflected on the packet (Phase 7 Slice 7H).

    Recording-only: never evidence and must not imply retrieval influence beyond ``influence``.
    """

    model_config = ConfigDict(extra="forbid")

    used: bool
    source: Literal["request_actor_context"] = "request_actor_context"
    recorded_context: ActorContext | None = None
    influence: ActorContextInfluence
    warnings: list[str] = Field(default_factory=list)


class RetrievalPacket(BaseModel):
    """Structured evidence routing output from the File Clerk."""

    packet_type: PacketType = "retrieval_packet"
    question: str
    interpreted_intent: InterpretedIntent
    selected_indexes: list[SelectedSemanticIndex]
    graph_paths: list[GraphPathPacket]
    evidence_units: list[EvidenceUnitPacket]
    alternative_interpretations: list[AlternativeInterpretation]
    context_budget: ContextBudgetSummary
    warnings: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    answer_mode: AnswerMode
    language_context: RetrievalLanguageContext | None = None
    actor_context: PacketActorContextRecording | None = None
