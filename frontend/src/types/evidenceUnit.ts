/** Mirrors `EvidenceUnitResponse` / `EvidenceUnitListResponse` from `app/schemas/evidence_unit.py`. */

export interface EvidenceUnitResponse {
  id: string;
  artifact_id: string;
  modality: string;
  content_type: string;
  text: string | null;
  location: Record<string, unknown> | null;
  source_fidelity: string;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface EvidenceUnitListResponse {
  items: EvidenceUnitResponse[];
}
