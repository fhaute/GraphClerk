/**
 * Mirrors backend graph schemas (`graph_node`, `graph_edge`, `graph_traversal`).
 * JSON datetimes are strings at runtime.
 */

export interface GraphNode {
  id: string;
  node_type: string;
  label: string;
  summary: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface GraphEdge {
  id: string;
  from_node_id: string;
  to_node_id: string;
  relation_type: string;
  summary: string | null;
  confidence: number | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface GraphNodeEvidenceRef {
  node_id: string;
  evidence_unit_id: string;
  support_type: string;
  confidence: number | null;
}

export interface GraphEdgeEvidenceRef {
  edge_id: string;
  evidence_unit_id: string;
  support_type: string;
  confidence: number | null;
}

/** Neighborhood payload from `GET /graph/nodes/{id}/neighborhood`. */
export interface GraphNeighborhood {
  start_node_id: string;
  depth: number;
  max_nodes: number;
  max_edges: number;
  relation_types: string[] | null;
  truncated: boolean;
  truncation_reasons: string[];
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_evidence: GraphNodeEvidenceRef[];
  edge_evidence: GraphEdgeEvidenceRef[];
}
