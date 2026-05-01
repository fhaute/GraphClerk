/** Matches backend `VersionResponse` (`GET /version`). */

export interface VersionResponse {
  name: string;
  version: string;
  phase: string;
}
