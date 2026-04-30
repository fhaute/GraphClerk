/**
 * Mirrors backend `app/schemas/retrieval_packet.py` (Phase 4 File Clerk).
 * Used for typed consumption of `POST /retrieve` responses only — no mock payloads.
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

/** Subset of options exposed in Query Playground; backend fills other defaults. */
export interface RetrieveOptionsPayload {
  max_evidence_units: number;
  max_graph_depth: number;
  include_alternatives: boolean;
}

export interface RetrieveRequestPayload {
  question: string;
  options?: RetrieveOptionsPayload | null;
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
}
