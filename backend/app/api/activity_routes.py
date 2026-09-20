from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authz import Permission, authorize_lead_access, require_permissions
from app.core.enums import ActivityType, AuditEventType
from app.db.session import get_db
from app.models.activity import Activity
from app.models.lead import Lead
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.services.activity import create_activity
from app.services.audit import record_audit

router = APIRouter(tags=["activities"])


@router.post(
    "/leads/{lead_id}/activities",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_activity(
    lead_id: int,
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.ACTIVITY_WRITE)),
) -> ActivityResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead, write=True)
    activity = create_activity(
        db,
        lead_id=lead_id,
        activity_type=ActivityType(payload.type.value),
        description=payload.description,
        metadata=payload.metadata,
    )
    db.flush()
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.ACTIVITY_ADDED,
        entity_type="activity",
        entity_id=activity.id,
        metadata={"lead_id": lead_id, "type": payload.type.value},
    )
    db.commit()
    db.refresh(activity)
    return ActivityResponse.model_validate(activity)


@router.get("/leads/{lead_id}/activities", response_model=list[ActivityResponse])
def list_activities(
    lead_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> list[ActivityResponse]:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead)
    activities = db.scalars(
        select(Activity)
        .where(Activity.lead_id == lead_id)
        .order_by(Activity.created_at.desc(), Activity.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [ActivityResponse.model_validate(item) for item in activities]


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> ActivityResponse:
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Activity not found")
    lead = db.get(Lead, activity.lead_id)
    if lead is not None:
        authorize_lead_access(current_user, lead)
    return ActivityResponse.model_validate(activity)
