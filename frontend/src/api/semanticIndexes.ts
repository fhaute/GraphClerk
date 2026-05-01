import { apiGetJson } from "./client";
import type {
  SemanticIndexEntryPointsResponse,
  SemanticIndexListResponse,
  SemanticIndexResponse,
  SemanticIndexSearchResponse,
} from "../types/semanticIndex";

/** Matches backend `GET /semantic-indexes` query: `limit` has `le=200`. */
const SEMANTIC_INDEX_LIST_LIMIT_MAX = 200;

export async function fetchSemanticIndexes(params?: {
  limit?: number;
  offset?: number;
}): Promise<SemanticIndexListResponse> {
  const q = new URLSearchParams();
  if (params?.limit != null) {
    const lim = Math.min(
      SEMANTIC_INDEX_LIST_LIMIT_MAX,
      Math.max(1, params.limit),
    );
    q.set("limit", String(lim));
  }
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  const raw = await apiGetJson<SemanticIndexListResponse | SemanticIndexResponse[]>(
    `/semantic-indexes${qs ? `?${qs}` : ""}`,
  );
  if (Array.isArray(raw)) return { items: raw };
  return { items: raw.items ?? [] };
}

export async function fetchSemanticIndex(
  semanticIndexId: string,
): Promise<SemanticIndexResponse> {
  const enc = encodeURIComponent(semanticIndexId);
  return apiGetJson<SemanticIndexResponse>(`/semantic-indexes/${enc}`);
}

export async function fetchSemanticIndexEntryPoints(
  semanticIndexId: string,
): Promise<SemanticIndexEntryPointsResponse> {
  const enc = encodeURIComponent(semanticIndexId);
  return apiGetJson<SemanticIndexEntryPointsResponse>(
    `/semantic-indexes/${enc}/entry-points`,
  );
}

export async function searchSemanticIndexes(
  query: string,
  limit: number,
): Promise<SemanticIndexSearchResponse> {
  const q = new URLSearchParams();
  q.set("q", query);
  q.set("limit", String(limit));
  return apiGetJson<SemanticIndexSearchResponse>(
    `/semantic-indexes/search?${q.toString()}`,
  );
}
