from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import ActivityType
from app.models.activity import Activity


def create_activity(
    db: Session,
    *,
    lead_id: int,
    activity_type: ActivityType,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> Activity:
    activity = Activity(
        lead_id=lead_id,
        type=activity_type,
        description=description,
        activity_metadata=metadata,
    )
    db.add(activity)
    return activity
