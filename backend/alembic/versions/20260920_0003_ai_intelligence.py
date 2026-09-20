"""Store the latest sales intelligence for each lead.

Revision ID: 20260920_0003
Revises: 20260920_0002
Create Date: 2026-09-20
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260920_0003"
down_revision: str | Sequence[str] | None = "20260920_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lead_intelligence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("qualification_summary", sa.Text(), nullable=False),
        sa.Column("buying_signals", sa.JSON(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("recommended_action", sa.String(length=200), nullable=False),
        sa.Column("recommended_action_reason", sa.Text(), nullable=False),
        sa.Column("recommended_action_priority", sa.String(length=20), nullable=False),
        sa.Column("follow_up_subject", sa.String(length=200), nullable=False),
        sa.Column("follow_up_message", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_intelligence_lead_id"), "lead_intelligence", ["lead_id"], unique=True)
    op.create_index(op.f("ix_lead_intelligence_generated_at"), "lead_intelligence", ["generated_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lead_intelligence_generated_at"), table_name="lead_intelligence")
    op.drop_index(op.f("ix_lead_intelligence_lead_id"), table_name="lead_intelligence")
    op.drop_table("lead_intelligence")
