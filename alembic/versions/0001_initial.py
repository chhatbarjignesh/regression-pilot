"""initial: create heal_events table

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "heal_events",
        sa.Column("run_id", sa.String(8), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Failure info
        sa.Column("test_name", sa.String(500), nullable=False),
        sa.Column("test_file", sa.String(500), nullable=False),
        sa.Column("framework", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text, nullable=False),
        sa.Column("stack_trace", sa.Text, nullable=False, server_default=""),
        sa.Column("repo_path", sa.String(500), nullable=False, server_default=""),
        sa.Column("branch", sa.String(255), nullable=False, server_default=""),
        sa.Column("commit_sha", sa.String(40), nullable=False, server_default=""),
        sa.Column("ci_build_url", sa.String(1000), nullable=False, server_default=""),
        # Classification + outcome
        sa.Column("failure_type", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("retries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.Text, nullable=False, server_default=""),
        # Fix details
        sa.Column("selector_before", sa.Text, nullable=False, server_default=""),
        sa.Column("selector_after", sa.Text, nullable=False, server_default=""),
        sa.Column("confidence", sa.Float, nullable=True),
        # Outputs
        sa.Column("jira_ticket", sa.String(50), nullable=False, server_default=""),
        sa.Column("pr_url", sa.String(1000), nullable=False, server_default=""),
        sa.Column("git_commit_sha", sa.String(40), nullable=False, server_default=""),
        sa.Column("time_saved_minutes", sa.Float, nullable=False, server_default="0"),
    )
    # Indexes for common dashboard queries
    op.create_index("ix_heal_events_status", "heal_events", ["status"])
    op.create_index("ix_heal_events_framework", "heal_events", ["framework"])
    op.create_index("ix_heal_events_created_at", "heal_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_heal_events_created_at", "heal_events")
    op.drop_index("ix_heal_events_framework", "heal_events")
    op.drop_index("ix_heal_events_status", "heal_events")
    op.drop_table("heal_events")
