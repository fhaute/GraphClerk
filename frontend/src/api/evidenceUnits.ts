import { apiGetJson } from "./client";
import type {
  EvidenceUnitListResponse,
  EvidenceUnitResponse,
} from "../types/evidenceUnit";

export async function fetchArtifactEvidence(
  artifactId: string,
  params?: { limit?: number; offset?: number },
): Promise<EvidenceUnitListResponse> {
  const enc = encodeURIComponent(artifactId);
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  return apiGetJson<EvidenceUnitListResponse>(
    `/artifacts/${enc}/evidence${qs ? `?${qs}` : ""}`,
  );
}

export async function fetchEvidenceUnit(
  evidenceUnitId: string,
): Promise<EvidenceUnitResponse> {
  const enc = encodeURIComponent(evidenceUnitId);
  return apiGetJson<EvidenceUnitResponse>(`/evidence-units/${enc}`);
}
