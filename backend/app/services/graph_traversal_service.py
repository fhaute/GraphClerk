from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import GraphRelationType
from app.models.graph_edge import GraphEdge
from app.models.graph_node import GraphNode
from app.repositories.graph_edge_evidence_repository import GraphEdgeEvidenceRepository
from app.repositories.graph_edge_repository import GraphEdgeRepository
from app.repositories.graph_node_evidence_repository import GraphNodeEvidenceRepository
from app.repositories.graph_node_repository import GraphNodeRepository
from app.services.errors import GraphNodeNotFoundError


@dataclass(frozen=True)
class GraphNeighborhood:
    start_node_id: uuid.UUID
    depth: int
    max_nodes: int
    max_edges: int
    relation_types: list[str] | None
    truncated: bool
    truncation_reasons: list[str]
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    node_evidence: list[tuple[uuid.UUID, uuid.UUID, str, float | None]]
    edge_evidence: list[tuple[uuid.UUID, uuid.UUID, str, float | None]]


class GraphTraversalService:
    """Bounded BFS neighborhood traversal (Phase 3 Slice I)."""

    def __init__(
        self,
        *,
        session: Session,
        node_repo: GraphNodeRepository | None = None,
        edge_repo: GraphEdgeRepository | None = None,
        node_ev_repo: GraphNodeEvidenceRepository | None = None,
        edge_ev_repo: GraphEdgeEvidenceRepository | None = None,
    ) -> None:
        self._session = session
        self._node_repo = node_repo or GraphNodeRepository(session)
        self._edge_repo = edge_repo or GraphEdgeRepository(session)
        self._node_ev_repo = node_ev_repo or GraphNodeEvidenceRepository(session)
        self._edge_ev_repo = edge_ev_repo or GraphEdgeEvidenceRepository(session)

    def neighborhood(
        self,
        *,
        start_node_id: uuid.UUID,
        depth: int = 1,
        max_nodes: int = 25,
        max_edges: int = 50,
        relation_types: list[str] | None = None,
    ) -> GraphNeighborhood:
        start = self._node_repo.get(start_node_id)
        if start is None:
            raise GraphNodeNotFoundError(f"GraphNode not found: {start_node_id}")

        # Validate relation types here (API also validates); keep service usable directly.
        if relation_types is not None:
            for rt in relation_types:
                GraphRelationType(rt)  # raises ValueError if invalid

        included_nodes: set[uuid.UUID] = {start_node_id}
        included_edges: list[GraphEdge] = []
        seen_edge_ids: set[uuid.UUID] = set()

        truncated = False
        reasons: list[str] = []

        frontier: list[uuid.UUID] = [start_node_id]

        for _level in range(depth):
            if not frontier:
                break

            # Deterministic expansion order.
            frontier = sorted(frontier, key=lambda x: str(x))

            edges = self._edge_repo.list_incident_edges(
                node_ids=frontier,
                relation_types=relation_types,
                limit=max_edges * 10,  # defensive; traversal enforces max_edges
            )

            # Deterministic edge processing order.
            edges = sorted(edges, key=lambda e: (str(e.from_node_id), str(e.to_node_id), str(e.relation_type), str(e.id)))

            next_frontier: list[uuid.UUID] = []
            for e in edges:
                if e.id in seen_edge_ids:
                    continue

                if len(included_edges) >= max_edges:
                    truncated = True
                    if "max_edges_reached" not in reasons:
                        reasons.append("max_edges_reached")
                    break

                a = e.from_node_id
                b = e.to_node_id
                a_in = a in included_nodes
                b_in = b in included_nodes

                # Consistency rule: do not include edges that reference missing nodes.
                if not a_in and not b_in:
                    # Edge incident to frontier should include at least one endpoint in frontier,
                    # but keep the rule strict anyway.
                    continue

                # If max_nodes reached, only include an edge if both endpoints already included.
                if len(included_nodes) >= max_nodes and not (a_in and b_in):
                    truncated = True
                    if "max_nodes_reached" not in reasons:
                        reasons.append("max_nodes_reached")
                    continue

                # If we need to add a new node, check capacity.
                if not a_in or not b_in:
                    if len(included_nodes) + 1 > max_nodes:
                        truncated = True
                        if "max_nodes_reached" not in reasons:
                            reasons.append("max_nodes_reached")
                        continue

                # Include edge.
                seen_edge_ids.add(e.id)
                included_edges.append(e)

                # Include nodes + expand frontier.
                if not a_in:
                    included_nodes.add(a)
                    next_frontier.append(a)
                if not b_in:
                    included_nodes.add(b)
                    next_frontier.append(b)

            frontier = next_frontier

        # Load nodes deterministically for response.
        nodes = self._node_repo.list_by_ids(list(included_nodes))
        nodes = sorted(nodes, key=lambda n: str(n.id))

        # Ensure edges list is deterministic and consistent with included nodes.
        edge_objs = [e for e in included_edges if e.from_node_id in included_nodes and e.to_node_id in included_nodes]
        edge_objs = sorted(edge_objs, key=lambda e: str(e.id))

        node_evs = self._node_ev_repo.list_by_graph_nodes([n.id for n in nodes])
        edge_evs = self._edge_ev_repo.list_by_graph_edges([e.id for e in edge_objs])

        node_evidence = [(x.graph_node_id, x.evidence_unit_id, x.support_type, x.confidence) for x in node_evs]
        edge_evidence = [(x.graph_edge_id, x.evidence_unit_id, x.support_type, x.confidence) for x in edge_evs]

        return GraphNeighborhood(
            start_node_id=start_node_id,
            depth=depth,
            max_nodes=max_nodes,
            max_edges=max_edges,
            relation_types=relation_types,
            truncated=truncated,
            truncation_reasons=reasons,
            nodes=nodes,
            edges=edge_objs,
            node_evidence=node_evidence,
            edge_evidence=edge_evidence,
        )

