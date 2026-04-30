import { apiGetJson } from "./client";
import type {
  RetrievalLogDetailResponse,
  RetrievalLogListResponse,
  RetrievalLogSummary,
} from "../types/retrievalLog";

export async function fetchRetrievalLogs(params: {
  limit: number;
  offset: number;
}): Promise<RetrievalLogListResponse> {
  const q = new URLSearchParams();
  q.set("limit", String(params.limit));
  q.set("offset", String(params.offset));
  const raw = await apiGetJson<RetrievalLogListResponse | RetrievalLogSummary[]>(
    `/retrieval-logs?${q.toString()}`,
  );
  if (Array.isArray(raw)) return { items: raw };
  return { items: raw.items ?? [] };
}

export async function fetchRetrievalLog(
  retrievalLogId: string,
): Promise<RetrievalLogDetailResponse> {
  const enc = encodeURIComponent(retrievalLogId);
  return apiGetJson<RetrievalLogDetailResponse>(`/retrieval-logs/${enc}`);
}
