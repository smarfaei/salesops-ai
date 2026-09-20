from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import PipelineStage, TaskStatus
from app.db.session import get_db
from app.models.lead import Lead
from app.models.task import SalesTask
from app.schemas.dashboard import DashboardKpis, DashboardSummary, MetricItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    """Return read-only aggregates without duplicating scoring or workflow rules."""
    leads = db.execute(
        select(Lead.status, Lead.pipeline_stage, Lead.score, Lead.budget)
    ).all()
    task_statuses = list(db.scalars(select(SalesTask.status)).all())

    status_counts = {name: 0 for name in ("Hot", "Warm", "Cold")}
    stage_counts = {stage.value: 0 for stage in PipelineStage}
    score_counts = {"0–39": 0, "40–69": 0, "70–100": 0}
    open_pipeline_value = 0

    for lead_status, stage, score, budget in leads:
        status_counts[lead_status] = status_counts.get(lead_status, 0) + 1
        stage_counts[stage.value] += 1
        if score >= 70:
            score_counts["70–100"] += 1
        elif score >= 40:
            score_counts["40–69"] += 1
        else:
            score_counts["0–39"] += 1
        if stage not in {PipelineStage.WON, PipelineStage.LOST}:
            open_pipeline_value += budget

    task_counts = {status.value: 0 for status in TaskStatus}
    for task_status in task_statuses:
        task_counts[task_status.value] += 1

    return DashboardSummary(
        kpis=DashboardKpis(
            total_leads=len(leads),
            hot_leads=status_counts["Hot"],
            qualified_leads=stage_counts[PipelineStage.QUALIFIED.value],
            open_pipeline_value=open_pipeline_value,
            won_leads=stage_counts[PipelineStage.WON.value],
            pending_tasks=task_counts[TaskStatus.PENDING.value],
        ),
        lead_status_distribution=[MetricItem(name=name, value=value) for name, value in status_counts.items()],
        pipeline_distribution=[MetricItem(name=name, value=value) for name, value in stage_counts.items()],
        score_distribution=[MetricItem(name=name, value=value) for name, value in score_counts.items()],
        task_status_distribution=[MetricItem(name=name.title(), value=value) for name, value in task_counts.items()],
    )
