import { apiGetJson } from "./client";
import type { HealthResponse } from "../types/health";

export function fetchHealth(): Promise<HealthResponse> {
  return apiGetJson<HealthResponse>("/health");
}
