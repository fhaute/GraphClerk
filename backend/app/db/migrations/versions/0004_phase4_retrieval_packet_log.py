"""Phase 4 retrieval log canonical packet snapshot.

Revision ID: 0004_phase4_retrieval_packet_log
Revises: 0003_phase3_graph_semantic_links
Create Date: 2026-04-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0004_phase4_retrieval_packet_log"
down_revision = "0003_phase3_graph_semantic_links"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "retrieval_log",
        sa.Column("retrieval_packet", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("retrieval_log", "retrieval_packet")
