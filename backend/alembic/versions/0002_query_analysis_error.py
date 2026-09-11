"""Add queries.analysis_error.

A stage 3 failure records its user-facing message here, so a row that never got
an analysis reads as failed rather than as still pending.

Revision ID: 0002_query_analysis_error
Revises: 0001_baseline
Create Date: 2026-09-11
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_query_analysis_error"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("queries", sa.Column("analysis_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("queries", "analysis_error")
