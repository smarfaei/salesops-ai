import logging
import math
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, or_, select, text
from sqlalchemy.orm import Session

from app.core.authz import Permission, authorize_lead_access, require_permissions
from app.core.demo import block_in_demo_mode
from app.core.enums import ActivityType, AuditEventType, PipelineStage, TaskStatus, UserRole
from app.db.session import get_db
from app.models.activity import Activity
from app.models.lead import Lead
from app.models.task import SalesTask
from app.schemas.activity import ActivityResponse
from app.schemas.lead import (
    HealthResponse,
    LeadCreate,
    LeadDetailResponse,
    LeadListResponse,
    LeadResponse,
    LeadOwnerUpdate,
    LeadStageUpdate,
    LeadUpdate,
)
from app.schemas.task import TaskResponse
from app.services.activity import create_activity
from app.services.pipeline import transition_stage
from app.services.scoring import score_lead
from app.models.user import User
from app.services.audit import record_audit

logger = logging.getLogger(__name__)
router = APIRouter()


class SortField(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"
    name = "name"
    company = "company"
    budget = "budget"
    employees = "employees"
    company_size = "company_size"
    score = "score"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


def _response(lead: Lead) -> LeadResponse:
    return LeadResponse.model_validate(lead)


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="connected")


@router.get("/leads", response_model=LeadListResponse, tags=["leads"])
def get_all_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=100),
    lead_status: str | None = Query(None, alias="status", max_length=50),
    pipeline_stage: PipelineStage | None = Query(None),
    min_score: int | None = Query(None, ge=0, le=100),
    max_score: int | None = Query(None, ge=0, le=100),
    sort_by: SortField = SortField.created_at,
    sort_order: SortOrder = SortOrder.desc,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> LeadListResponse:
    filters = []
    if current_user.role == UserRole.SALES_REP:
        filters.append(Lead.owner_user_id == current_user.id)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(or_(Lead.name.ilike(pattern), Lead.company.ilike(pattern), Lead.need.ilike(pattern)))
    if lead_status:
        normalized = lead_status.strip().title().removesuffix(" Lead")
        if normalized not in {"Hot", "Warm", "Cold"}:
            raise HTTPException(422, "Status must be Hot, Warm, or Cold")
        filters.append(Lead.status == normalized)
    if pipeline_stage:
        filters.append(Lead.pipeline_stage == pipeline_stage)
    if min_score is not None:
        filters.append(Lead.score >= min_score)
    if max_score is not None:
        filters.append(Lead.score <= max_score)
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(422, "min_score cannot be greater than max_score")

    total = db.scalar(select(func.count()).select_from(Lead).where(*filters)) or 0
    sort_column = Lead.employees if sort_by == SortField.company_size else getattr(Lead, sort_by.value)
    order = asc(sort_column) if sort_order == SortOrder.asc else desc(sort_column)
    query = (
        select(Lead)
        .where(*filters)
        .order_by(order, Lead.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(query).all())
    return LeadListResponse(
        items=[_response(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED, tags=["leads"])
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    _demo_guard: None = Depends(block_in_demo_mode),
    current_user: User = Depends(require_permissions(Permission.LEAD_CREATE)),
) -> LeadResponse:
    result = score_lead(payload.budget, payload.employees, payload.need)
    lead = Lead(**payload.model_dump(), score=result.score, status=result.status, score_reasons=result.reasons)
    db.add(lead)
    db.flush()
    create_activity(
        db,
        lead_id=lead.id,
        activity_type=ActivityType.LEAD_CREATED,
        description=f"Lead created for {lead.name} at {lead.company}",
        metadata={"score": lead.score, "status": lead.status},
    )
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.LEAD_CREATED,
        entity_type="lead",
        entity_id=lead.id,
    )
    db.commit()
    db.refresh(lead)
    logger.info("Created lead id=%s status=%s score=%s", lead.id, lead.status, lead.score)
    return _response(lead)


@router.get("/leads/{lead_id}", response_model=LeadResponse, tags=["leads"])
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> LeadResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead)
    return _response(lead)


@router.get("/leads/{lead_id}/detail", response_model=LeadDetailResponse, tags=["leads"])
def get_lead_detail(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> LeadDetailResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead)
    recent_activities = list(
        db.scalars(
            select(Activity)
            .where(Activity.lead_id == lead_id)
            .order_by(Activity.created_at.desc(), Activity.id.desc())
            .limit(20)
        ).all()
    )
    now = datetime.now(timezone.utc)
    upcoming_tasks = list(
        db.scalars(
            select(SalesTask)
            .where(
                SalesTask.lead_id == lead_id,
                SalesTask.status == TaskStatus.PENDING,
                SalesTask.due_at >= now,
            )
            .order_by(SalesTask.due_at.asc(), SalesTask.id.asc())
            .limit(10)
        ).all()
    )
    return LeadDetailResponse(
        lead=_response(lead),
        recent_activities=[ActivityResponse.model_validate(item) for item in recent_activities],
        upcoming_tasks=[TaskResponse.model_validate(item) for item in upcoming_tasks],
    )


@router.patch("/leads/{lead_id}/stage", response_model=LeadResponse, tags=["pipeline"])
def change_lead_stage(
    lead_id: int,
    payload: LeadStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.PIPELINE_WRITE)),
) -> LeadResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead, write=True)
    previous = lead.pipeline_stage
    if not transition_stage(db, lead, payload.stage):
        raise HTTPException(status.HTTP_409_CONFLICT, "Lead is already in this stage")
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.PIPELINE_CHANGED,
        entity_type="lead",
        entity_id=lead.id,
        metadata={"from": previous.value, "to": payload.stage.value},
    )
    db.commit()
    db.refresh(lead)
    logger.info("Changed lead id=%s stage=%s", lead.id, lead.pipeline_stage.value)
    return _response(lead)


@router.patch("/leads/{lead_id}", response_model=LeadResponse, tags=["leads"])
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    _demo_guard: None = Depends(block_in_demo_mode),
    current_user: User = Depends(require_permissions(Permission.LEAD_EDIT)),
) -> LeadResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead, write=True)

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields provided for update")
    changes = {}
    for field, value in updates.items():
        previous = getattr(lead, field)
        if previous != value:
            changes[field] = {"from": previous, "to": value}
            setattr(lead, field, value)

    result = score_lead(lead.budget, lead.employees, lead.need)
    lead.score = result.score
    lead.status = result.status
    lead.score_reasons = result.reasons
    if changes:
        create_activity(
            db,
            lead_id=lead.id,
            activity_type=ActivityType.LEAD_UPDATED,
            description=f"Lead updated: {', '.join(changes)}",
            metadata={"changes": changes},
        )
        record_audit(
            db,
            actor_user_id=current_user.id,
            event_type=AuditEventType.LEAD_UPDATED,
            entity_type="lead",
            entity_id=lead.id,
            metadata={"fields": list(changes)},
        )
    db.commit()
    db.refresh(lead)
    logger.info("Updated lead id=%s status=%s score=%s", lead.id, lead.status, lead.score)
    return _response(lead)


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["leads"])
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _demo_guard: None = Depends(block_in_demo_mode),
    current_user: User = Depends(require_permissions(Permission.LEAD_DELETE)),
) -> Response:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead, write=True)
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.LEAD_DELETED,
        entity_type="lead",
        entity_id=lead.id,
        metadata={"company": lead.company},
    )
    db.delete(lead)
    db.commit()
    logger.info("Deleted lead id=%s", lead_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/leads/{lead_id}/owner", response_model=LeadResponse, tags=["leads"])
def assign_lead_owner(
    lead_id: int,
    payload: LeadOwnerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_ASSIGN)),
) -> LeadResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    owner = db.get(User, payload.owner_user_id) if payload.owner_user_id is not None else None
    if payload.owner_user_id is not None and (
        owner is None or not owner.is_active or owner.role != UserRole.SALES_REP
    ):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Owner must be an active sales rep")
    previous = lead.owner_user_id
    lead.owner = owner
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.OWNER_CHANGED,
        entity_type="lead",
        entity_id=lead.id,
        metadata={"from": previous, "to": payload.owner_user_id},
    )
    db.commit()
    db.refresh(lead)
    return _response(lead)
