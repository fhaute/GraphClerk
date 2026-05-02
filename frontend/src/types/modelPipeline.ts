/** GET /model-pipeline/config — read-only operator projection (Track D D7b). */

export type ModelPipelineGlobalAdapter =
  | "not_configured"
  | "deterministic_test"
  | "ollama"
  | "openai_compatible";

export type ModelPipelinePurposeWireStatus =
  | "disabled"
  | "configured"
  | "misconfigured"
  | "policy_blocked";

export interface ModelPipelinePurposeRow {
  enabled: boolean;
  allowed: boolean;
  adapter: string | null;
  model: string | null;
  timeout_seconds: number | null;
  output_kind: string;
  status: ModelPipelinePurposeWireStatus;
}

export interface ModelPipelinePurposeRegistryBlock {
  evidence_candidate_enricher: ModelPipelinePurposeRow;
  artifact_classifier: ModelPipelinePurposeRow;
  extraction_helper: ModelPipelinePurposeRow;
  routing_hint_generator: ModelPipelinePurposeRow;
}

export interface ModelPipelineConfigResponse {
  adapter: ModelPipelineGlobalAdapter;
  base_url_configured: boolean;
  model_configured: boolean;
  timeout_seconds: number;
  purpose_registry: ModelPipelinePurposeRegistryBlock;
  warnings: string[];
}
