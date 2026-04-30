/** Mirrors `ArtifactResponse` / `ArtifactListResponse` from backend `app/schemas/artifact.py`. */

export interface ArtifactResponse {
  id: string;
  filename: string;
  title: string | null;
  artifact_type: string;
  mime_type: string | null;
  storage_uri: string;
  checksum: string | null;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown> | null;
}

export interface ArtifactListResponse {
  items: ArtifactResponse[];
}
