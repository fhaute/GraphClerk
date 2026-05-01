/**
 * Mirrors backend `app/schemas/retrieval_packet.py` and `app/schemas/retrieval.py`
 * (Phase 4 File Clerk + Phase 7 context recording on the packet).
 * Used for typed consumption of `POST /retrieve` — no mock payloads.
 */

export type PacketType = "retrieval_packet";

export type IntentType =
  | "explain"
  | "compare"
  | "locate"
  | "summarize"
  | "debug"
  | "recommend"
  | "unknown";

export type AnswerMode =
  | "answer_with_evidence"
  | "answer_with_caveats"
  | "ask_clarification"
  | "not_enough_evidence"
  | "conflicting_evidence"
  | "unsupported";

export interface InterpretedIntent {
  intent_type: IntentType;
  confidence: number;
  notes: string[];
}

export interface SelectedSemanticIndex {
  semantic_index_id: string;
  meaning: string;
  score: number;
  selection_reason: string;
}

export interface GraphPathPacket {
  start_node_id: string;
  nodes: string[];
  edges: string[];
  depth: number;
}

export interface EvidenceUnitPacket {
  evidence_unit_id: string;
  artifact_id: string;
  modality: string;
  content_type: string;
  source_fidelity: string;
  text?: string | null;
  location?: Record<string, unknown> | null;
  selection_reason: string;
  confidence?: number | null;
}

export interface EvidenceLanguageAggregateRow {
  language: string;
  evidence_unit_count: number;
  average_confidence?: number | null;
  min_confidence?: number | null;
  max_confidence?: number | null;
}

/** Phase 7 — derived from selected evidence `metadata_json` only; not translation; not evidence. */
export interface RetrievalLanguageContext {
  version: number;
  source: string;
  query_language?: string | null;
  evidence_languages: EvidenceLanguageAggregateRow[];
  primary_evidence_language?: string | null;
  distinct_evidence_language_count: number;
  evidence_units_without_language_metadata_count: number;
  warnings: string[];
}

export interface AlternativeInterpretation {
  if_user_meant: string;
  suggested_semantic_indexes: string[];
  reason: string;
}

export interface ContextBudgetSummary {
  max_evidence_units: number;
  selected_evidence_units: number;
  pruned_evidence_units: number;
  pruning_reasons: string[];
  max_graph_paths?: number | null;
  max_selected_indexes?: number | null;
}

/** Optional `POST /retrieve` request metadata (Phase 7); validated server-side; not used for routing. */
export interface ActorContext {
  actor_id?: string | null;
  actor_type?: string | null;
  role?: string | null;
  expertise_level?: string | null;
  preferred_language?: string | null;
  purpose?: string | null;
  metadata?: Record<string, unknown> | null;
}

/** Subset of options exposed in Query Playground; backend fills other defaults. */
export interface RetrieveOptionsPayload {
  max_evidence_units: number;
  max_graph_depth: number;
  include_alternatives: boolean;
}

export interface RetrieveRequestPayload {
  question: string;
  options?: RetrieveOptionsPayload | null;
  /** Optional; omitted when unset. Recording-only on the packet in the current baseline. */
  actor_context?: ActorContext | null;
}

export type ActorContextInfluence = "none" | "recorded_only_no_route_boost_applied";

/** Phase 7 — how request actor context was reflected on the packet. */
export interface PacketActorContextRecording {
  used: boolean;
  source: string;
  recorded_context?: ActorContext | null;
  influence: ActorContextInfluence;
  warnings: string[];
}

export interface RetrievalPacket {
  packet_type: PacketType;
  question: string;
  interpreted_intent: InterpretedIntent;
  selected_indexes: SelectedSemanticIndex[];
  graph_paths: GraphPathPacket[];
  evidence_units: EvidenceUnitPacket[];
  alternative_interpretations: AlternativeInterpretation[];
  context_budget: ContextBudgetSummary;
  warnings: string[];
  confidence: number;
  answer_mode: AnswerMode;
  language_context?: RetrievalLanguageContext | null;
  actor_context?: PacketActorContextRecording | null;
}
