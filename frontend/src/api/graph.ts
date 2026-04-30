import { apiGetJson } from "./client";
import type {
  GraphEdge,
  GraphNeighborhood,
  GraphNode,
} from "../types/graph";

interface GraphNodeListBody {
  items?: GraphNode[];
}

interface GraphEdgeListBody {
  items?: GraphEdge[];
}

function normalizeNodeList(raw: GraphNodeListBody | GraphNode[]): GraphNode[] {
  if (Array.isArray(raw)) return raw;
  return raw.items ?? [];
}

function normalizeEdgeList(raw: GraphEdgeListBody | GraphEdge[]): GraphEdge[] {
  if (Array.isArray(raw)) return raw;
  return raw.items ?? [];
}

export async function fetchGraphNodes(params?: {
  limit?: number;
  offset?: number;
}): Promise<GraphNode[]> {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  const raw = await apiGetJson<GraphNodeListBody | GraphNode[]>(
    `/graph/nodes${qs ? `?${qs}` : ""}`,
  );
  return normalizeNodeList(raw);
}

export async function fetchGraphNode(nodeId: string): Promise<GraphNode> {
  const enc = encodeURIComponent(nodeId);
  return apiGetJson<GraphNode>(`/graph/nodes/${enc}`);
}

export async function fetchGraphEdges(params?: {
  limit?: number;
  offset?: number;
}): Promise<GraphEdge[]> {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  const raw = await apiGetJson<GraphEdgeListBody | GraphEdge[]>(
    `/graph/edges${qs ? `?${qs}` : ""}`,
  );
  return normalizeEdgeList(raw);
}

export async function fetchGraphEdge(edgeId: string): Promise<GraphEdge> {
  const enc = encodeURIComponent(edgeId);
  return apiGetJson<GraphEdge>(`/graph/edges/${enc}`);
}

export async function fetchGraphNeighborhood(
  nodeId: string,
  params: {
    depth: number;
    max_nodes: number;
    max_edges: number;
    relation_types?: string[] | null;
  },
): Promise<GraphNeighborhood> {
  const enc = encodeURIComponent(nodeId);
  const q = new URLSearchParams();
  q.set("depth", String(params.depth));
  q.set("max_nodes", String(params.max_nodes));
  q.set("max_edges", String(params.max_edges));
  if (params.relation_types?.length) {
    for (const rt of params.relation_types) {
      q.append("relation_types", rt);
    }
  }
  return apiGetJson<GraphNeighborhood>(
    `/graph/nodes/${enc}/neighborhood?${q.toString()}`,
  );
}
