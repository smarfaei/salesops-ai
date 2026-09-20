"""Create the initial leads table.

Revision ID: 20260920_0001
Revises:
Create Date: 2026-09-20
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260920_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("leads"):
        op.create_table(
            "leads",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("company", sa.String(length=100), nullable=False),
            sa.Column("employees", sa.Integer(), nullable=False),
            sa.Column("need", sa.String(length=500), nullable=False),
            sa.Column("budget", sa.Integer(), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("score_reasons", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        # Adopt databases created by the pre-Alembic version without losing leads.
        columns = {column["name"] for column in inspector.get_columns("leads")}
        with op.batch_alter_table("leads") as batch_op:
            if "score_reasons" not in columns:
                batch_op.add_column(sa.Column("score_reasons", sa.JSON(), nullable=True))
            if "created_at" not in columns:
                batch_op.add_column(
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
                )
            if "updated_at" not in columns:
                batch_op.add_column(
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
                )

        if "score_reasons" not in columns:
            leads = sa.table(
                "leads",
                sa.column("id", sa.Integer()),
                sa.column("budget", sa.Integer()),
                sa.column("employees", sa.Integer()),
                sa.column("need", sa.String()),
                sa.column("score", sa.Integer()),
                sa.column("status", sa.String()),
                sa.column("score_reasons", sa.JSON()),
            )
            for row in bind.execute(sa.select(leads.c.id, leads.c.budget, leads.c.employees, leads.c.need)):
                score, status, reasons = _score_legacy_lead(row.budget, row.employees, row.need)
                bind.execute(
                    leads.update()
                    .where(leads.c.id == row.id)
                    .values(score=score, status=status, score_reasons=reasons)
                )
            with op.batch_alter_table("leads") as batch_op:
                batch_op.alter_column("score_reasons", existing_type=sa.JSON(), nullable=False)

    inspector = sa.inspect(bind)
    existing_indexes = {index["name"] for index in inspector.get_indexes("leads")}
    for name, column in (
        (op.f("ix_leads_id"), "id"),
        (op.f("ix_leads_name"), "name"),
        (op.f("ix_leads_company"), "company"),
        (op.f("ix_leads_score"), "score"),
        (op.f("ix_leads_status"), "status"),
    ):
        if name not in existing_indexes:
            op.create_index(name, "leads", [column], unique=False)


def _score_legacy_lead(budget: int, employees: int, need: str) -> tuple[int, str, list[str]]:
    score = 0
    reasons: list[str] = []
    if budget >= 5000:
        score += 50
        reasons.append("High budget: +50")
    elif budget >= 2000:
        score += 30
        reasons.append("Medium budget: +30")
    elif budget >= 1000:
        score += 15
        reasons.append("Qualified budget: +15")
    else:
        reasons.append("Budget below scoring threshold: +0")
    if employees >= 100:
        score += 30
        reasons.append("Large company: +30")
    elif employees >= 20:
        score += 20
        reasons.append("Growing company: +20")
    elif employees >= 5:
        score += 10
        reasons.append("Small company: +10")
    else:
        reasons.append("Company size below scoring threshold: +0")
    if "AI" in need.upper():
        score += 20
        reasons.append("AI requirement detected: +20")
    else:
        reasons.append("No AI requirement detected: +0")
    status = "Hot" if score >= 70 else "Warm" if score >= 40 else "Cold"
    return score, status, reasons


def downgrade() -> None:
    op.drop_index(op.f("ix_leads_status"), table_name="leads")
    op.drop_index(op.f("ix_leads_score"), table_name="leads")
    op.drop_index(op.f("ix_leads_company"), table_name="leads")
    op.drop_index(op.f("ix_leads_name"), table_name="leads")
    op.drop_index(op.f("ix_leads_id"), table_name="leads")
    op.drop_table("leads")
