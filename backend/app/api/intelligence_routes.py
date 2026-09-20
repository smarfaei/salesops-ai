from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authz import Permission, authorize_lead_access, require_permissions
from app.core.enums import AuditEventType
from app.db.session import get_db
from app.models.intelligence import LeadIntelligence
from app.models.lead import Lead
from app.models.user import User
from app.schemas.intelligence import LeadIntelligenceResponse
from app.services.intelligence import (
    IntelligenceUnavailable,
    SalesIntelligenceService,
    get_sales_intelligence_service,
    intelligence_to_response,
)
from app.services.audit import record_audit

router = APIRouter(tags=["sales intelligence"])


@router.post("/leads/{lead_id}/intelligence", response_model=LeadIntelligenceResponse)
def generate_intelligence(
    lead_id: int,
    db: Session = Depends(get_db),
    service: SalesIntelligenceService = Depends(get_sales_intelligence_service),
    current_user: User = Depends(require_permissions(Permission.INTELLIGENCE_WRITE)),
) -> LeadIntelligenceResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead, write=True)
    existed = db.scalar(select(LeadIntelligence.id).where(LeadIntelligence.lead_id == lead_id))
    try:
        record = service.generate_for_lead(db, lead)
    except IntelligenceUnavailable as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sales intelligence provider is unavailable",
        ) from exc
    record_audit(
        db,
        actor_user_id=current_user.id,
        event_type=AuditEventType.INTELLIGENCE_GENERATED,
        entity_type="lead_intelligence",
        entity_id=record.id,
        metadata={"lead_id": lead_id, "regenerated": existed is not None, "provider": record.provider},
    )
    db.commit()
    db.refresh(record)
    return intelligence_to_response(record)


@router.get("/leads/{lead_id}/intelligence", response_model=LeadIntelligenceResponse)
def get_intelligence(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.LEAD_READ)),
) -> LeadIntelligenceResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    authorize_lead_access(current_user, lead)
    record = db.scalar(select(LeadIntelligence).where(LeadIntelligence.lead_id == lead_id))
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sales intelligence has not been generated")
    return intelligence_to_response(record)
