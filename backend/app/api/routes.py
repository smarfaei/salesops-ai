import logging
import math
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, or_, select, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lead import Lead
from app.schemas.lead import HealthResponse, LeadCreate, LeadListResponse, LeadResponse, LeadUpdate
from app.services.scoring import score_lead

logger = logging.getLogger(__name__)
router = APIRouter()


class SortField(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"
    name = "name"
    company = "company"
    budget = "budget"
    employees = "employees"
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
    sort_by: SortField = SortField.created_at,
    sort_order: SortOrder = SortOrder.desc,
    db: Session = Depends(get_db),
) -> LeadListResponse:
    filters = []
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(or_(Lead.name.ilike(pattern), Lead.company.ilike(pattern), Lead.need.ilike(pattern)))
    if lead_status:
        normalized = lead_status.strip().title().removesuffix(" Lead")
        if normalized not in {"Hot", "Warm", "Cold"}:
            raise HTTPException(422, "Status must be Hot, Warm, or Cold")
        filters.append(Lead.status == normalized)

    total = db.scalar(select(func.count()).select_from(Lead).where(*filters)) or 0
    sort_column = getattr(Lead, sort_by.value)
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
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> LeadResponse:
    result = score_lead(payload.budget, payload.employees, payload.need)
    lead = Lead(**payload.model_dump(), score=result.score, status=result.status, score_reasons=result.reasons)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    logger.info("Created lead id=%s status=%s score=%s", lead.id, lead.status, lead.score)
    return _response(lead)


@router.get("/leads/{lead_id}", response_model=LeadResponse, tags=["leads"])
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    return _response(lead)


@router.patch("/leads/{lead_id}", response_model=LeadResponse, tags=["leads"])
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)) -> LeadResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields provided for update")
    for field, value in updates.items():
        setattr(lead, field, value)

    result = score_lead(lead.budget, lead.employees, lead.need)
    lead.score = result.score
    lead.status = result.status
    lead.score_reasons = result.reasons
    db.commit()
    db.refresh(lead)
    logger.info("Updated lead id=%s status=%s score=%s", lead.id, lead.status, lead.score)
    return _response(lead)


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["leads"])
def delete_lead(lead_id: int, db: Session = Depends(get_db)) -> Response:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    db.delete(lead)
    db.commit()
    logger.info("Deleted lead id=%s", lead_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
