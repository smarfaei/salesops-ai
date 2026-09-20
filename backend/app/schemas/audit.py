from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AuditEventType
from app.schemas.user import UserSummary


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int | None
    event_type: AuditEventType
    entity_type: str
    entity_id: str | None
    metadata: dict[str, Any] | None = Field(validation_alias="audit_metadata")
    created_at: datetime
    actor: UserSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int
