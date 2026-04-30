import { apiPostJson } from "./client";
import type {
  RetrievalPacket,
  RetrieveRequestPayload,
} from "../types/retrievalPacket";

export async function postRetrieve(
  payload: RetrieveRequestPayload,
): Promise<RetrievalPacket> {
  return apiPostJson<RetrievalPacket>("/retrieve", payload);
}
