import { apiGetJson } from "./client";
import type { VersionResponse } from "../types/version";

export async function fetchVersion(): Promise<VersionResponse> {
  return apiGetJson<VersionResponse>("/version");
}
