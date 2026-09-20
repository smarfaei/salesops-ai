from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ActivityType, ManualActivityType


class ActivityCreate(BaseModel):
    type: ManualActivityType
    description: str = Field(min_length=1, max_length=1000)
    metadata: dict[str, Any] | None = None

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class ActivityResponse(BaseModel):
    id: int
    lead_id: int
    type: ActivityType
    description: str
    metadata: dict[str, Any] | None = Field(validation_alias="activity_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
