import { apiGetJson } from "./client";
import type { ArtifactListResponse, ArtifactResponse } from "../types/artifact";

export async function fetchArtifacts(params?: {
  limit?: number;
  offset?: number;
}): Promise<ArtifactListResponse> {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  return apiGetJson<ArtifactListResponse>(`/artifacts${qs ? `?${qs}` : ""}`);
}

export async function fetchArtifact(artifactId: string): Promise<ArtifactResponse> {
  const enc = encodeURIComponent(artifactId);
  return apiGetJson<ArtifactResponse>(`/artifacts/${enc}`);
}
