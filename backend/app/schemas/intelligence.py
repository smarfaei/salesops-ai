from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import PipelineStage, TaskPriority


class EvidenceSignal(BaseModel):
    signal: str = Field(min_length=1, max_length=200)
    evidence: str = Field(min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")


class NextBestAction(BaseModel):
    action: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=1000)
    priority: TaskPriority

    model_config = ConfigDict(extra="forbid")


class FollowUpMessage(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=3000)

    model_config = ConfigDict(extra="forbid")


class SalesIntelligence(BaseModel):
    qualification_summary: str = Field(min_length=1, max_length=1500)
    buying_signals: list[EvidenceSignal]
    risks: list[EvidenceSignal]
    next_best_action: NextBestAction
    follow_up: FollowUpMessage

    model_config = ConfigDict(extra="forbid")


class ActivityContext(BaseModel):
    type: str
    description: str
    created_at: datetime


class TaskContext(BaseModel):
    title: str
    status: str
    priority: str
    due_at: datetime


class IntelligenceContext(BaseModel):
    lead_id: int
    name: str
    company: str
    employees: int
    need: str
    budget: int
    score: int
    qualification_status: str
    pipeline_stage: PipelineStage
    recent_activities: list[ActivityContext]
    open_tasks: list[TaskContext]
    generated_at: datetime


class LeadIntelligenceResponse(SalesIntelligence):
    id: int
    lead_id: int
    generated_at: datetime
    provider: str
    model: str | None
    provider_metadata: dict | None

    model_config = ConfigDict(from_attributes=True)
