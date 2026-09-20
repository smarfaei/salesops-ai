"""Add sales pipeline, activities, and follow-up tasks.

Revision ID: 20260920_0002
Revises: 20260920_0001
Create Date: 2026-09-20
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260920_0002"
down_revision: str | Sequence[str] | None = "20260920_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

pipeline_stage = sa.Enum(
    "New", "Qualified", "Contacted", "Proposal", "Won", "Lost",
    name="pipeline_stage", native_enum=False, create_constraint=True,
)
activity_type = sa.Enum(
    "lead_created", "lead_updated", "stage_changed", "call", "email", "meeting", "note",
    name="activity_type", native_enum=False, create_constraint=True,
)
task_status = sa.Enum(
    "pending", "completed", "cancelled",
    name="task_status", native_enum=False, create_constraint=True,
)
task_priority = sa.Enum(
    "low", "medium", "high",
    name="task_priority", native_enum=False, create_constraint=True,
)


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("pipeline_stage", pipeline_stage, server_default="New", nullable=False),
    )
    op.create_index(op.f("ix_leads_pipeline_stage"), "leads", ["pipeline_stage"], unique=False)

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("type", activity_type, nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activities_lead_id"), "activities", ["lead_id"], unique=False)
    op.create_index(op.f("ix_activities_type"), "activities", ["type"], unique=False)
    op.create_index(op.f("ix_activities_created_at"), "activities", ["created_at"], unique=False)
    op.create_index("ix_activities_lead_created", "activities", ["lead_id", "created_at"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", task_status, server_default="pending", nullable=False),
        sa.Column("priority", task_priority, server_default="medium", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_lead_id"), "tasks", ["lead_id"], unique=False)
    op.create_index(op.f("ix_tasks_due_at"), "tasks", ["due_at"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_priority"), "tasks", ["priority"], unique=False)
    op.create_index("ix_tasks_lead_due", "tasks", ["lead_id", "due_at"], unique=False)
    op.create_index("ix_tasks_status_due", "tasks", ["status", "due_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_status_due", table_name="tasks")
    op.drop_index("ix_tasks_lead_due", table_name="tasks")
    op.drop_index(op.f("ix_tasks_priority"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_due_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_lead_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_activities_lead_created", table_name="activities")
    op.drop_index(op.f("ix_activities_created_at"), table_name="activities")
    op.drop_index(op.f("ix_activities_type"), table_name="activities")
    op.drop_index(op.f("ix_activities_lead_id"), table_name="activities")
    op.drop_table("activities")
    op.drop_index(op.f("ix_leads_pipeline_stage"), table_name="leads")
    with op.batch_alter_table("leads") as batch_op:
        batch_op.drop_column("pipeline_stage")
