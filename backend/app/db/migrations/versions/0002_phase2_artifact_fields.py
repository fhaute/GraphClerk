"""Phase 2 artifact raw source fields.

Revision ID: 0002_phase2_artifact_fields
Revises: 0001_phase1_core_models
Create Date: 2026-04-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0002_phase2_artifact_fields"
down_revision = "0001_phase1_core_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artifact", sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("artifact", sa.Column("raw_text", sa.Text(), nullable=True))
    op.alter_column("artifact", "size_bytes", server_default=None)


def downgrade() -> None:
    op.drop_column("artifact", "raw_text")
    op.drop_column("artifact", "size_bytes")

