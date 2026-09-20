from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import PipelineStage
from app.schemas.activity import ActivityResponse
from app.schemas.task import TaskResponse
from app.schemas.user import UserSummary


class LeadBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    company: str = Field(min_length=1, max_length=100)
    employees: int = Field(ge=0)
    need: str = Field(min_length=1, max_length=500)
    budget: int = Field(ge=0)

    @field_validator("name", "company", "need")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    company: str | None = Field(default=None, min_length=1, max_length=100)
    employees: int | None = Field(default=None, ge=0)
    need: str | None = Field(default=None, min_length=1, max_length=500)
    budget: int | None = Field(default=None, ge=0)

    @field_validator("name", "company", "need")
    @classmethod
    def reject_blank_or_null_text(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("must not be null")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("employees", "budget")
    @classmethod
    def reject_null_numbers(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("must not be null")
        return value


class LeadResponse(LeadBase):
    id: int
    score: int = Field(ge=0, le=100)
    status: str
    score_reasons: list[str]
    pipeline_stage: PipelineStage
    owner_user_id: int | None
    owner: UserSummary | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadListResponse(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    page_size: int
    pages: int


class LeadStageUpdate(BaseModel):
    stage: PipelineStage


class LeadOwnerUpdate(BaseModel):
    owner_user_id: int | None


class LeadDetailResponse(BaseModel):
    lead: LeadResponse
    recent_activities: list[ActivityResponse]
    upcoming_tasks: list[TaskResponse]


class HealthResponse(BaseModel):
    status: str
    database: str
