"""Add users, ownership, refresh tokens, and audit logs.

Revision ID: 20260920_0004
Revises: 20260920_0003
Create Date: 2026-09-20
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260920_0004"
down_revision: str | Sequence[str] | None = "20260920_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("hashed_password", sa.String(length=512), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "sales_manager",
                "sales_rep",
                "viewer",
                name="user_role",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.add_column("leads", sa.Column("owner_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_leads_owner_user_id_users",
        "leads",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_leads_owner_user_id"), "leads", ["owner_user_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["replaced_by_id"], ["refresh_tokens.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_expires_at"), "refresh_tokens", ["expires_at"])
    op.create_index(op.f("ix_refresh_tokens_revoked_at"), "refresh_tokens", ["revoked_at"])
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "login_succeeded",
                "lead_created",
                "lead_updated",
                "lead_deleted",
                "owner_changed",
                "pipeline_changed",
                "task_created",
                "task_completed",
                "task_cancelled",
                "activity_added",
                "intelligence_generated",
                "user_created",
                "user_activated",
                "user_deactivated",
                "role_changed",
                name="audit_event_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"])
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"])
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"])
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"])
    op.create_index(op.f("ix_audit_logs_event_type"), "audit_logs", ["event_type"])


def downgrade() -> None:
    for name in (
        "ix_audit_logs_event_type",
        "ix_audit_logs_entity_type",
        "ix_audit_logs_entity_id",
        "ix_audit_logs_created_at",
        "ix_audit_logs_actor_user_id",
    ):
        op.drop_index(name, table_name="audit_logs")
    op.drop_table("audit_logs")
    for name in (
        "ix_refresh_tokens_user_id",
        "ix_refresh_tokens_token_hash",
        "ix_refresh_tokens_revoked_at",
        "ix_refresh_tokens_expires_at",
    ):
        op.drop_index(name, table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index(op.f("ix_leads_owner_user_id"), table_name="leads")
    op.drop_constraint("fk_leads_owner_user_id_users", "leads", type_="foreignkey")
    op.drop_column("leads", "owner_user_id")
    for name in ("ix_users_role", "ix_users_is_active", "ix_users_id", "ix_users_email"):
        op.drop_index(name, table_name="users")
    op.drop_table("users")
