from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.intelligence import LeadIntelligence
from app.models.lead import Lead
from app.schemas.intelligence import LeadIntelligenceResponse
from app.services.intelligence import (
    IntelligenceUnavailable,
    SalesIntelligenceService,
    get_sales_intelligence_service,
    intelligence_to_response,
)

router = APIRouter(tags=["sales intelligence"])


@router.post("/leads/{lead_id}/intelligence", response_model=LeadIntelligenceResponse)
def generate_intelligence(
    lead_id: int,
    db: Session = Depends(get_db),
    service: SalesIntelligenceService = Depends(get_sales_intelligence_service),
) -> LeadIntelligenceResponse:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    try:
        record = service.generate_for_lead(db, lead)
    except IntelligenceUnavailable as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Sales intelligence provider is unavailable",
        ) from exc
    db.commit()
    db.refresh(record)
    return intelligence_to_response(record)


@router.get("/leads/{lead_id}/intelligence", response_model=LeadIntelligenceResponse)
def get_intelligence(lead_id: int, db: Session = Depends(get_db)) -> LeadIntelligenceResponse:
    if db.get(Lead, lead_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    record = db.scalar(select(LeadIntelligence).where(LeadIntelligence.lead_id == lead_id))
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sales intelligence has not been generated")
    return intelligence_to_response(record)
