import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import {
  fetchGraphEdge,
  fetchGraphEdges,
  fetchGraphNeighborhood,
  fetchGraphNode,
  fetchGraphNodes,
} from "../api/graph";
import type { GraphEdge, GraphNeighborhood, GraphNode } from "../types/graph";

function formatError(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function clampInt(n: number, min: number, max: number, fallback: number): number {
  if (Number.isNaN(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

export function GraphExplorer() {
  const [nodesLoading, setNodesLoading] = useState(true);
  const [edgesLoading, setEdgesLoading] = useState(true);
  const [nodesError, setNodesError] = useState<string | null>(null);
  const [edgesError, setEdgesError] = useState<string | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nodeDetailLoading, setNodeDetailLoading] = useState(false);
  const [nodeDetailError, setNodeDetailError] = useState<string | null>(null);
  const [nodeDetail, setNodeDetail] = useState<GraphNode | null>(null);

  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [edgeDetailLoading, setEdgeDetailLoading] = useState(false);
  const [edgeDetailError, setEdgeDetailError] = useState<string | null>(null);
  const [edgeDetail, setEdgeDetail] = useState<GraphEdge | null>(null);

  const [nbDepth, setNbDepth] = useState("1");
  const [nbMaxNodes, setNbMaxNodes] = useState("25");
  const [nbMaxEdges, setNbMaxEdges] = useState("50");
  const [nbLoading, setNbLoading] = useState(false);
  const [nbError, setNbError] = useState<string | null>(null);
  const [neighborhood, setNeighborhood] = useState<GraphNeighborhood | null>(null);

  useEffect(() => {
    let cancelled = false;
    setNodesLoading(true);
    setNodesError(null);
    fetchGraphNodes({ limit: 300 })
      .then((items) => {
        if (!cancelled) setNodes(items);
      })
      .catch((e) => {
        if (!cancelled) setNodesError(formatError(e));
      })
      .finally(() => {
        if (!cancelled) setNodesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setEdgesLoading(true);
    setEdgesError(null);
    fetchGraphEdges({ limit: 300 })
      .then((items) => {
        if (!cancelled) setEdges(items);
      })
      .catch((e) => {
        if (!cancelled) setEdgesError(formatError(e));
      })
      .finally(() => {
        if (!cancelled) setEdgesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectNode = useCallback(async (nodeId: string) => {
    setSelectedNodeId(nodeId);
    setSelectedEdgeId(null);
    setEdgeDetail(null);
    setEdgeDetailError(null);
    setNeighborhood(null);
    setNbError(null);
    setNodeDetailLoading(true);
    setNodeDetailError(null);
    setNodeDetail(null);
    try {
      const n = await fetchGraphNode(nodeId);
      setNodeDetail(n);
    } catch (e) {
      setNodeDetailError(formatError(e));
    } finally {
      setNodeDetailLoading(false);
    }
  }, []);

  const selectEdge = useCallback(async (edgeId: string) => {
    setSelectedEdgeId(edgeId);
    setEdgeDetailLoading(true);
    setEdgeDetailError(null);
    setEdgeDetail(null);
    try {
      const e = await fetchGraphEdge(edgeId);
      setEdgeDetail(e);
    } catch (err) {
      setEdgeDetailError(formatError(err));
    } finally {
      setEdgeDetailLoading(false);
    }
  }, []);

  const loadNeighborhood = useCallback(async () => {
    if (!selectedNodeId) return;
    const depth = clampInt(Number.parseInt(nbDepth, 10), 1, 3, 1);
    const maxNodes = clampInt(Number.parseInt(nbMaxNodes, 10), 1, 500, 25);
    const maxEdges = clampInt(Number.parseInt(nbMaxEdges, 10), 1, 5000, 50);
    setNbDepth(String(depth));
    setNbMaxNodes(String(maxNodes));
    setNbMaxEdges(String(maxEdges));
    setNbLoading(true);
    setNbError(null);
    setNeighborhood(null);
    try {
      const n = await fetchGraphNeighborhood(selectedNodeId, {
        depth,
        max_nodes: maxNodes,
        max_edges: maxEdges,
      });
      setNeighborhood(n);
    } catch (e) {
      setNbError(formatError(e));
    } finally {
      setNbLoading(false);
    }
  }, [selectedNodeId, nbDepth, nbMaxNodes, nbMaxEdges]);

  const listsLoaded = !nodesLoading && !edgesLoading;
  const graphEmpty =
    listsLoaded && !nodesError && !edgesError && nodes.length === 0 && edges.length === 0;

  return (
    <section className="space-y-6">
      <div className="rounded-md border border-neutral-300 bg-neutral-100 px-3 py-2 text-sm text-neutral-800">
        <strong className="font-medium">Read-only graph inspection</strong>
        <p className="mt-1 text-xs text-neutral-700">
          This UI only displays nodes, edges, and neighborhood payloads returned by the API. It does{" "}
          <strong className="font-medium">not</strong> imply automatic graph extraction or an editor.
          Evidence rows below are <strong className="font-medium">support references</strong> (ids +
          support metadata only), not full EvidenceUnit bodies — open an evidence unit in{" "}
          <span className="font-medium">Artifacts &amp; evidence</span> if you need text payloads.
        </p>
      </div>

      {graphEmpty && (
        <p className="rounded-md border border-neutral-200 bg-white px-3 py-3 text-sm text-neutral-700">
          The API returned no graph nodes and no edges (empty graph for this deployment).
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-medium text-neutral-700">Nodes</h2>
          <p className="mt-1 text-xs text-neutral-500">
            <code className="font-mono">GET /graph/nodes</code>,{" "}
            <code className="font-mono">GET /graph/nodes/{"{id}"}</code>
          </p>
          {nodesLoading && <p className="mt-4 text-sm text-neutral-600">Loading nodes…</p>}
          {nodesError && (
            <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
              {nodesError}
            </p>
          )}
          {!nodesLoading && !nodesError && nodes.length === 0 && !graphEmpty && (
            <p className="mt-4 text-sm text-neutral-600">No nodes in list response.</p>
          )}
          {!nodesLoading && nodes.length > 0 && (
            <ul className="mt-4 max-h-64 divide-y divide-neutral-100 overflow-y-auto rounded border border-neutral-100">
              {nodes.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => void selectNode(n.id)}
                    className={`flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left text-sm hover:bg-neutral-50 ${
                      selectedNodeId === n.id ? "bg-neutral-100" : ""
                    }`}
                  >
                    <span className="font-mono text-xs text-neutral-500">{n.id}</span>
                    <span className="font-medium text-neutral-900">{n.label}</span>
                    <span className="text-xs text-neutral-600">{n.node_type}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
          <h2 className="text-sm font-medium text-neutral-700">Edges</h2>
          <p className="mt-1 text-xs text-neutral-500">
            <code className="font-mono">GET /graph/edges</code>,{" "}
            <code className="font-mono">GET /graph/edges/{"{id}"}</code>
          </p>
          {edgesLoading && <p className="mt-4 text-sm text-neutral-600">Loading edges…</p>}
          {edgesError && (
            <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
              {edgesError}
            </p>
          )}
          {!edgesLoading && !edgesError && edges.length === 0 && !graphEmpty && (
            <p className="mt-4 text-sm text-neutral-600">No edges in list response.</p>
          )}
          {!edgesLoading && edges.length > 0 && (
            <ul className="mt-4 max-h-64 divide-y divide-neutral-100 overflow-y-auto rounded border border-neutral-100">
              {edges.map((e) => (
                <li key={e.id}>
                  <button
                    type="button"
                    onClick={() => void selectEdge(e.id)}
                    className={`flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left text-sm hover:bg-neutral-50 ${
                      selectedEdgeId === e.id ? "bg-neutral-100" : ""
                    }`}
                  >
                    <span className="font-mono text-xs text-neutral-500">{e.id}</span>
                    <span className="text-xs text-neutral-800">
                      <span className="font-mono">{e.from_node_id}</span>
                      {" → "}
                      <span className="font-mono">{e.to_node_id}</span>
                    </span>
                    <span className="text-xs text-neutral-600">{e.relation_type}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {selectedNodeId && (
        <div className="space-y-4">
          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Selected node detail</h3>
            {nodeDetailLoading && (
              <p className="mt-3 text-sm text-neutral-600">Loading node…</p>
            )}
            {nodeDetailError && (
              <p className="mt-3 whitespace-pre-wrap text-sm text-red-800">{nodeDetailError}</p>
            )}
            {!nodeDetailLoading && nodeDetail && (
              <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-[minmax(8rem,auto)_1fr]">
                <dt className="text-neutral-500">id</dt>
                <dd className="font-mono text-xs">{nodeDetail.id}</dd>
                <dt className="text-neutral-500">node_type</dt>
                <dd>{nodeDetail.node_type}</dd>
                <dt className="text-neutral-500">label</dt>
                <dd>{nodeDetail.label}</dd>
                <dt className="text-neutral-500">summary</dt>
                <dd className="whitespace-pre-wrap">{nodeDetail.summary ?? "(none)"}</dd>
                <dt className="text-neutral-500">metadata</dt>
                <dd className="whitespace-pre-wrap font-mono text-xs">
                  {nodeDetail.metadata == null || Object.keys(nodeDetail.metadata).length === 0
                    ? "(none)"
                    : formatJson(nodeDetail.metadata)}
                </dd>
                <dt className="text-neutral-500">created_at</dt>
                <dd className="font-mono text-xs">{nodeDetail.created_at}</dd>
                <dt className="text-neutral-500">updated_at</dt>
                <dd className="font-mono text-xs">{nodeDetail.updated_at}</dd>
              </dl>
            )}
          </div>

          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Neighborhood</h3>
            <p className="mt-1 text-xs text-neutral-500">
              <code className="font-mono">
                GET /graph/nodes/{"{node_id}"}/neighborhood
              </code>
            </p>
            <div className="mt-4 flex flex-wrap items-end gap-3">
              <label className="flex flex-col text-xs text-neutral-600">
                depth (1–3)
                <input
                  type="number"
                  min={1}
                  max={3}
                  className="mt-1 w-20 rounded border border-neutral-300 px-2 py-1 text-sm shadow-sm"
                  value={nbDepth}
                  onChange={(e) => setNbDepth(e.target.value)}
                  disabled={nbLoading}
                />
              </label>
              <label className="flex flex-col text-xs text-neutral-600">
                max_nodes (1–500)
                <input
                  type="number"
                  min={1}
                  max={500}
                  className="mt-1 w-24 rounded border border-neutral-300 px-2 py-1 text-sm shadow-sm"
                  value={nbMaxNodes}
                  onChange={(e) => setNbMaxNodes(e.target.value)}
                  disabled={nbLoading}
                />
              </label>
              <label className="flex flex-col text-xs text-neutral-600">
                max_edges (1–5000)
                <input
                  type="number"
                  min={1}
                  max={5000}
                  className="mt-1 w-28 rounded border border-neutral-300 px-2 py-1 text-sm shadow-sm"
                  value={nbMaxEdges}
                  onChange={(e) => setNbMaxEdges(e.target.value)}
                  disabled={nbLoading}
                />
              </label>
              <button
                type="button"
                className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-50"
                onClick={() => void loadNeighborhood()}
                disabled={nbLoading}
              >
                {nbLoading ? "Loading…" : "Load neighborhood"}
              </button>
            </div>

            {nbError && (
              <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
                {nbError}
              </p>
            )}

            {neighborhood && (
              <div className="mt-6 space-y-4">
                {neighborhood.truncated && (
                  <div className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950">
                    <strong className="font-medium">Truncated</strong>
                    <p className="mt-1 text-xs">
                      The API reported <code className="font-mono">truncated=true</code>. Reasons:
                    </p>
                    <ul className="mt-2 list-inside list-disc text-xs">
                      {neighborhood.truncation_reasons.length === 0 ? (
                        <li>(no reasons listed)</li>
                      ) : (
                        neighborhood.truncation_reasons.map((r, i) => (
                          <li key={i} className="whitespace-pre-wrap">
                            {r}
                          </li>
                        ))
                      )}
                    </ul>
                  </div>
                )}

                {!neighborhood.truncated && neighborhood.truncation_reasons.length > 0 && (
                  <p className="text-xs text-neutral-600">
                    truncation_reasons:{" "}
                    {neighborhood.truncation_reasons.join(" · ") || "(empty)"}
                  </p>
                )}

                <div className="text-xs text-neutral-600">
                  start_node_id:{" "}
                  <code className="font-mono">{neighborhood.start_node_id}</code> · depth cap{" "}
                  {neighborhood.depth} · max_nodes {neighborhood.max_nodes} · max_edges{" "}
                  {neighborhood.max_edges}
                  {neighborhood.relation_types?.length ? (
                    <>
                      {" "}
                      · relation_types: {neighborhood.relation_types.join(", ")}
                    </>
                  ) : null}
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-neutral-700">
                    Neighborhood nodes ({neighborhood.nodes.length})
                  </h4>
                  {neighborhood.nodes.length === 0 ? (
                    <p className="mt-2 text-sm text-neutral-600">
                      No nodes in this neighborhood payload.
                    </p>
                  ) : (
                    <ul className="mt-2 space-y-2">
                      {neighborhood.nodes.map((n) => (
                        <li
                          key={n.id}
                          className="rounded border border-neutral-100 bg-neutral-50 px-2 py-2 text-xs"
                        >
                          <div className="font-mono text-neutral-600">{n.id}</div>
                          <div className="font-medium text-neutral-900">{n.label}</div>
                          <div className="text-neutral-600">{n.node_type}</div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-neutral-700">
                    Neighborhood edges ({neighborhood.edges.length})
                  </h4>
                  {neighborhood.edges.length === 0 ? (
                    <p className="mt-2 text-sm text-neutral-600">
                      No edges in this neighborhood response.
                    </p>
                  ) : (
                    <ul className="mt-2 space-y-2">
                      {neighborhood.edges.map((e) => (
                        <li
                          key={e.id}
                          className="rounded border border-neutral-100 bg-neutral-50 px-2 py-2 text-xs"
                        >
                          <div className="font-mono text-neutral-600">{e.id}</div>
                          <div>
                            <span className="font-mono">{e.from_node_id}</span>
                            {" → "}
                            <span className="font-mono">{e.to_node_id}</span>
                          </div>
                          <div>{e.relation_type}</div>
                          {e.confidence != null && (
                            <div className="text-neutral-600">confidence: {e.confidence}</div>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="rounded border border-blue-200 bg-blue-50 px-3 py-3">
                  <h4 className="text-xs font-semibold text-blue-950">
                    Node evidence support refs ({neighborhood.node_evidence.length})
                  </h4>
                  <p className="mt-1 text-xs text-blue-900">
                    API fields only — link node ↔ evidence_unit_id; no evidence text or artifact
                    labels are implied here.
                  </p>
                  {neighborhood.node_evidence.length === 0 ? (
                    <p className="mt-2 text-sm text-blue-950">
                      No node_evidence entries in this neighborhood response.
                    </p>
                  ) : (
                    <table className="mt-3 w-full border-collapse text-left text-xs">
                      <thead>
                        <tr className="border-b border-blue-200 text-blue-900">
                          <th className="py-1 pr-2 font-medium">node_id</th>
                          <th className="py-1 pr-2 font-medium">evidence_unit_id</th>
                          <th className="py-1 pr-2 font-medium">support_type</th>
                          <th className="py-1 font-medium">confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {neighborhood.node_evidence.map((r, i) => (
                          <tr key={`${r.node_id}-${r.evidence_unit_id}-${i}`} className="border-b border-blue-100">
                            <td className="py-1 pr-2 font-mono break-all">{r.node_id}</td>
                            <td className="py-1 pr-2 font-mono break-all">{r.evidence_unit_id}</td>
                            <td className="py-1 pr-2">{r.support_type}</td>
                            <td className="py-1">{r.confidence ?? "(none)"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                <div className="rounded border border-blue-200 bg-blue-50 px-3 py-3">
                  <h4 className="text-xs font-semibold text-blue-950">
                    Edge evidence support refs ({neighborhood.edge_evidence.length})
                  </h4>
                  <p className="mt-1 text-xs text-blue-900">
                    API fields only — link edge ↔ evidence_unit_id; no inferred narrative.
                  </p>
                  {neighborhood.edge_evidence.length === 0 ? (
                    <p className="mt-2 text-sm text-blue-950">
                      No edge_evidence entries in this neighborhood response.
                    </p>
                  ) : (
                    <table className="mt-3 w-full border-collapse text-left text-xs">
                      <thead>
                        <tr className="border-b border-blue-200 text-blue-900">
                          <th className="py-1 pr-2 font-medium">edge_id</th>
                          <th className="py-1 pr-2 font-medium">evidence_unit_id</th>
                          <th className="py-1 pr-2 font-medium">support_type</th>
                          <th className="py-1 font-medium">confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {neighborhood.edge_evidence.map((r, i) => (
                          <tr key={`${r.edge_id}-${r.evidence_unit_id}-${i}`} className="border-b border-blue-100">
                            <td className="py-1 pr-2 font-mono break-all">{r.edge_id}</td>
                            <td className="py-1 pr-2 font-mono break-all">{r.evidence_unit_id}</td>
                            <td className="py-1 pr-2">{r.support_type}</td>
                            <td className="py-1">{r.confidence ?? "(none)"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedEdgeId && (
        <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-medium text-neutral-700">Selected edge detail</h3>
          {edgeDetailLoading && (
            <p className="mt-3 text-sm text-neutral-600">Loading edge…</p>
          )}
          {edgeDetailError && (
            <p className="mt-3 whitespace-pre-wrap text-sm text-red-800">{edgeDetailError}</p>
          )}
          {!edgeDetailLoading && edgeDetail && (
            <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-[minmax(8rem,auto)_1fr]">
              <dt className="text-neutral-500">id</dt>
              <dd className="font-mono text-xs">{edgeDetail.id}</dd>
              <dt className="text-neutral-500">from_node_id</dt>
              <dd className="font-mono text-xs">{edgeDetail.from_node_id}</dd>
              <dt className="text-neutral-500">to_node_id</dt>
              <dd className="font-mono text-xs">{edgeDetail.to_node_id}</dd>
              <dt className="text-neutral-500">relation_type</dt>
              <dd>{edgeDetail.relation_type}</dd>
              <dt className="text-neutral-500">summary</dt>
              <dd className="whitespace-pre-wrap">{edgeDetail.summary ?? "(none)"}</dd>
              <dt className="text-neutral-500">confidence</dt>
              <dd>{edgeDetail.confidence ?? "(none)"}</dd>
              <dt className="text-neutral-500">metadata</dt>
              <dd className="whitespace-pre-wrap font-mono text-xs">
                {edgeDetail.metadata == null || Object.keys(edgeDetail.metadata).length === 0
                  ? "(none)"
                  : formatJson(edgeDetail.metadata)}
              </dd>
              <dt className="text-neutral-500">created_at</dt>
              <dd className="font-mono text-xs">{edgeDetail.created_at}</dd>
              <dt className="text-neutral-500">updated_at</dt>
              <dd className="font-mono text-xs">{edgeDetail.updated_at}</dd>
            </dl>
          )}
        </div>
      )}
    </section>
  );
}
