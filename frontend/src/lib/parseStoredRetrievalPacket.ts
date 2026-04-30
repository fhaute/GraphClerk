import type { RetrievalPacket } from "../types/retrievalPacket";

/** Minimal structural check before using stored JSON as a `RetrievalPacket`. */
export function parseStoredRetrievalPacket(raw: unknown): RetrievalPacket | null {
  if (raw == null || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  if (o.packet_type !== "retrieval_packet") return null;
  if (typeof o.question !== "string") return null;
  if (!Array.isArray(o.evidence_units)) return null;
  if (!Array.isArray(o.graph_paths)) return null;
  if (!Array.isArray(o.selected_indexes)) return null;
  if (!Array.isArray(o.alternative_interpretations)) return null;
  if (!Array.isArray(o.warnings)) return null;
  if (o.interpreted_intent == null || typeof o.interpreted_intent !== "object") return null;
  if (o.context_budget == null || typeof o.context_budget !== "object") return null;
  if (typeof o.answer_mode !== "string") return null;
  if (typeof o.confidence !== "number") return null;
  return o as unknown as RetrievalPacket;
}
