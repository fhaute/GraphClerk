"""Phase 3 graph evidence links and semantic index entry nodes.

Revision ID: 0003_phase3_graph_semantic_links
Revises: 0002_phase2_artifact_fields
Create Date: 2026-04-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0003_phase3_graph_semantic_links"
down_revision = "0002_phase2_artifact_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add vector indexing state to SemanticIndex.
    op.add_column(
        "semantic_index",
        sa.Column("vector_status", sa.String(length=16), nullable=False, server_default="pending"),
    )
    op.create_check_constraint(
        "ck_semantic_index_vector_status_allowed",
        "semantic_index",
        "vector_status IN ('pending','indexed','failed')",
    )
    op.alter_column("semantic_index", "vector_status", server_default=None)

    op.create_table(
        "graph_node_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("graph_node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("support_type", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["graph_node_id"], ["graph_node.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_unit_id"], ["evidence_unit.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "graph_node_id",
            "evidence_unit_id",
            "support_type",
            name="uq_graph_node_evidence_node_ev_support",
        ),
    )
    op.create_index("ix_graph_node_evidence_graph_node_id", "graph_node_evidence", ["graph_node_id"])
    op.create_index("ix_graph_node_evidence_evidence_unit_id", "graph_node_evidence", ["evidence_unit_id"])

    op.create_table(
        "graph_edge_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("graph_edge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("support_type", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["graph_edge_id"], ["graph_edge.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evidence_unit_id"], ["evidence_unit.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "graph_edge_id",
            "evidence_unit_id",
            "support_type",
            name="uq_graph_edge_evidence_edge_ev_support",
        ),
    )
    op.create_index("ix_graph_edge_evidence_graph_edge_id", "graph_edge_evidence", ["graph_edge_id"])
    op.create_index("ix_graph_edge_evidence_evidence_unit_id", "graph_edge_evidence", ["evidence_unit_id"])

    op.create_table(
        "semantic_index_entry_node",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("semantic_index_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graph_node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["semantic_index_id"], ["semantic_index.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["graph_node_id"], ["graph_node.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "semantic_index_id",
            "graph_node_id",
            name="uq_semantic_index_entry_node",
        ),
    )
    op.create_index(
        "ix_semantic_index_entry_node_semantic_index_id",
        "semantic_index_entry_node",
        ["semantic_index_id"],
    )
    op.create_index(
        "ix_semantic_index_entry_node_graph_node_id",
        "semantic_index_entry_node",
        ["graph_node_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_semantic_index_entry_node_graph_node_id", table_name="semantic_index_entry_node")
    op.drop_index("ix_semantic_index_entry_node_semantic_index_id", table_name="semantic_index_entry_node")
    op.drop_table("semantic_index_entry_node")

    op.drop_index("ix_graph_edge_evidence_evidence_unit_id", table_name="graph_edge_evidence")
    op.drop_index("ix_graph_edge_evidence_graph_edge_id", table_name="graph_edge_evidence")
    op.drop_table("graph_edge_evidence")

    op.drop_index("ix_graph_node_evidence_evidence_unit_id", table_name="graph_node_evidence")
    op.drop_index("ix_graph_node_evidence_graph_node_id", table_name="graph_node_evidence")
    op.drop_table("graph_node_evidence")

    op.drop_constraint("ck_semantic_index_vector_status_allowed", "semantic_index", type_="check")
    op.drop_column("semantic_index", "vector_status")

