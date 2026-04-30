/**
 * Mirrors backend `app/schemas/semantic_index.py`.
 * Search results match `SemanticIndexSearchResult`; list wrapper matches artifact list style.
 */

export interface SemanticIndexResponse {
  id: string;
  meaning: string;
  summary: string | null;
  embedding_text: string | null;
  entry_node_ids: string[];
  vector_status: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SemanticIndexListResponse {
  items: SemanticIndexResponse[];
}

export interface SemanticIndexEntryPointsResponse {
  entry_node_ids: string[];
}

export interface SemanticIndexSearchResult extends SemanticIndexResponse {
  score: number;
}

export interface SemanticIndexSearchResponse {
  results: SemanticIndexSearchResult[];
}
