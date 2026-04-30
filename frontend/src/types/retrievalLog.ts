/**
 * Mirrors `backend/app/schemas/retrieval_log.py`.
 * Datetimes are ISO strings in JSON.
 */

export interface RetrievalLogSummary {
  id: string;
  question: string;
  confidence: number | null;
  warnings: string[] | null;
  latency_ms: number | null;
  token_estimate: number | null;
  evidence_unit_count: number;
  has_retrieval_packet: boolean;
  created_at: string;
}

export interface RetrievalLogListResponse {
  items: RetrievalLogSummary[];
}

export interface RetrievalLogDetailResponse {
  id: string;
  question: string;
  selected_indexes: Record<string, unknown>[] | null;
  graph_path: Record<string, unknown> | null;
  evidence_unit_ids: string[] | null;
  confidence: number | null;
  warnings: string[] | null;
  latency_ms: number | null;
  token_estimate: number | null;
  metadata: Record<string, unknown> | null;
  retrieval_packet: Record<string, unknown> | null;
  created_at: string;
}
