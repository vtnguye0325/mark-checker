"""Baseline schema: users and queries.

This revision holds the schema as it stood before ``queries.analysis_error``.
A database that predates Alembic already has these tables, so stamp it with
this revision instead of running it. ``mark_checker.core.db.run_migrations``
does that stamp on its own.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-11
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("google_sub", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("picture", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_sub"),
    )
    op.create_table(
        "queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("mark", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("nice_class", sa.Integer(), nullable=False),
        sa.Column("translation", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("pseudo_mark", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("prob_distinctive", sa.Float(), nullable=True),
        sa.Column("formatted_input", sa.Text(), nullable=True),
        sa.Column("attributions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_queries_user_id_created_at",
        "queries",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_queries_user_id_created_at", table_name="queries")
    op.drop_table("queries")
    op.drop_table("users")
