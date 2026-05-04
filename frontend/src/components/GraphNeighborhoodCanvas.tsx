import { memo, useCallback, useEffect } from "react";
import type { MouseEvent } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  Handle,
  Position,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { GraphEdge, GraphNode, GraphNeighborhood } from "../types/graph";

export type GraphNeighborhoodCanvasProps = {
  neighborhood: GraphNeighborhood;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
};

type GraphExplorerNodeData = {
  label: string;
  nodeType: string;
  isCenter: boolean;
};

function layoutNeighborhood(
  nodes: GraphNode[],
  edges: GraphEdge[],
  startNodeId: string,
): Map<string, { x: number; y: number }> {
  const nodeIds = new Set(nodes.map((n) => n.id));
  const adj = new Map<string, string[]>();
  for (const id of nodeIds) adj.set(id, []);
  for (const e of edges) {
    if (!nodeIds.has(e.from_node_id) || !nodeIds.has(e.to_node_id)) continue;
    adj.get(e.from_node_id)!.push(e.to_node_id);
    adj.get(e.to_node_id)!.push(e.from_node_id);
  }

  const depth = new Map<string, number>();
  const queue: string[] = [];
  if (nodeIds.has(startNodeId)) {
    depth.set(startNodeId, 0);
    queue.push(startNodeId);
  }
  while (queue.length > 0) {
    const u = queue.shift()!;
    const du = depth.get(u)!;
    for (const v of adj.get(u) ?? []) {
      if (!depth.has(v)) {
        depth.set(v, du + 1);
        queue.push(v);
      }
    }
  }

  const UNREACH = 1_000;
  for (const n of nodes) {
    if (!depth.has(n.id)) depth.set(n.id, UNREACH);
  }

  const byDepth = new Map<number, string[]>();
  for (const n of nodes) {
    const d = depth.get(n.id)!;
    if (!byDepth.has(d)) byDepth.set(d, []);
    byDepth.get(d)!.push(n.id);
  }

  const center = { x: 380, y: 300 };
  const positions = new Map<string, { x: number; y: number }>();
  positions.set(startNodeId, center);

  const sortedDepths = Array.from(byDepth.keys()).sort((a, b) => a - b);
  for (const d of sortedDepths) {
    if (d === 0) continue;
    const ids = (byDepth.get(d) ?? []).filter((id) => id !== startNodeId).sort();
    if (ids.length === 0) continue;

    if (d === UNREACH) {
      const gap = 160;
      const rowY = center.y + 220;
      ids.forEach((id, i) => {
        positions.set(id, {
          x: center.x + (i - (ids.length - 1) / 2) * gap,
          y: rowY,
        });
      });
      continue;
    }

    const radius = 110 + (d - 1) * 95;
    ids.forEach((id, i) => {
      const angle = (2 * Math.PI * i) / ids.length - Math.PI / 2;
      positions.set(id, {
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle),
      });
    });
  }

  return positions;
}

function buildRfNodes(
  graphNodes: GraphNode[],
  positions: Map<string, { x: number; y: number }>,
  startNodeId: string,
  selectedNodeId: string | null,
): Node<GraphExplorerNodeData>[] {
  return graphNodes.map((n) => {
    const pos = positions.get(n.id) ?? { x: 0, y: 0 };
    return {
      id: n.id,
      type: "graphExplorerNode",
      position: pos,
      data: {
        label: n.label,
        nodeType: n.node_type,
        isCenter: n.id === startNodeId,
      },
      selected: selectedNodeId === n.id,
    };
  });
}

function buildRfEdges(graphNodes: GraphNode[], graphEdges: GraphEdge[]): Edge[] {
  const nodeIds = new Set(graphNodes.map((n) => n.id));
  return graphEdges
    .filter((e) => nodeIds.has(e.from_node_id) && nodeIds.has(e.to_node_id))
    .map((e) => ({
      id: e.id,
      source: e.from_node_id,
      target: e.to_node_id,
      label: e.relation_type,
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      style: { stroke: "#737373", strokeWidth: 1.25 },
      labelStyle: { fill: "#404040", fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: "#fafafa", fillOpacity: 0.95 },
      labelBgPadding: [4, 2] as [number, number],
      labelBgBorderRadius: 4,
    }));
}

const GraphExplorerNode = memo(function GraphExplorerNode({
  data,
  selected,
}: NodeProps<Node<GraphExplorerNodeData>>) {
  const center = data.isCenter;
  return (
    <div
      className={`min-w-[132px] max-w-[220px] rounded-lg border px-2.5 py-2 shadow-sm ${
        center
          ? "border-neutral-900 bg-neutral-900 text-white"
          : selected
            ? "border-blue-500 bg-white ring-2 ring-blue-300"
            : "border-neutral-200 bg-white text-neutral-900"
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-0 !bg-neutral-400"
      />
      <div
        className={`text-[10px] font-semibold uppercase tracking-wide ${
          center ? "text-neutral-300" : "text-neutral-500"
        }`}
      >
        {data.nodeType}
      </div>
      <div
        className={`mt-0.5 text-sm font-medium leading-snug ${
          center ? "text-white" : "text-neutral-900"
        }`}
      >
        {data.label}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-0 !bg-neutral-400"
      />
    </div>
  );
});

const nodeTypes = { graphExplorerNode: GraphExplorerNode };

function NeighborhoodFlowInner({
  neighborhood,
  selectedNodeId,
  onSelectNode,
}: GraphNeighborhoodCanvasProps) {
  const { fitView } = useReactFlow();
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState<Node<GraphExplorerNodeData>>([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    const positions = layoutNeighborhood(
      neighborhood.nodes,
      neighborhood.edges,
      neighborhood.start_node_id,
    );
    setRfNodes(buildRfNodes(neighborhood.nodes, positions, neighborhood.start_node_id, selectedNodeId));
    setRfEdges(buildRfEdges(neighborhood.nodes, neighborhood.edges));
  }, [neighborhood, selectedNodeId, setRfNodes, setRfEdges]);

  useEffect(() => {
    const t = requestAnimationFrame(() => {
      fitView({ padding: 0.15, duration: 200 });
    });
    return () => cancelAnimationFrame(t);
  }, [neighborhood, fitView]);

  const onNodeClick = useCallback(
    (_: MouseEvent, node: Node) => {
      onSelectNode(node.id);
    },
    [onSelectNode],
  );

  return (
    <div className="h-[min(420px,55vh)] min-h-[280px] w-full rounded-md border border-neutral-200 bg-neutral-50">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        fitView
        proOptions={{ hideAttribution: true }}
        className="rounded-md"
      >
        <Background gap={14} size={1} color="#d4d4d4" />
        <Controls className="!shadow-md" showInteractive={false} />
        <MiniMap
          nodeStrokeWidth={2}
          zoomable
          pannable
          className="!rounded-md !border !border-neutral-200 !bg-white"
        />
      </ReactFlow>
    </div>
  );
}

export function GraphNeighborhoodCanvas(props: GraphNeighborhoodCanvasProps) {
  return (
    <ReactFlowProvider>
      <NeighborhoodFlowInner {...props} />
    </ReactFlowProvider>
  );
}
