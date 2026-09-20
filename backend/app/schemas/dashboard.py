from pydantic import BaseModel


class MetricItem(BaseModel):
    name: str
    value: int


class DashboardKpis(BaseModel):
    total_leads: int
    hot_leads: int
    qualified_leads: int
    open_pipeline_value: int
    won_leads: int
    pending_tasks: int


class DashboardSummary(BaseModel):
    kpis: DashboardKpis
    lead_status_distribution: list[MetricItem]
    pipeline_distribution: list[MetricItem]
    score_distribution: list[MetricItem]
    task_status_distribution: list[MetricItem]
