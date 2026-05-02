import { apiGetJson } from "./client";
import type { ModelPipelineConfigResponse } from "../types/modelPipeline";

export async function getModelPipelineConfig(): Promise<ModelPipelineConfigResponse> {
  return apiGetJson<ModelPipelineConfigResponse>("/model-pipeline/config");
}
