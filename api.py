from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base, Lead


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Sales Agent API",
    version="2.1.0"
)


# -------------------------
# Pydantic Schemas
# -------------------------

class LeadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    company: str = Field(min_length=1, max_length=100)
    employees: int = Field(ge=0)
    need: str = Field(min_length=1, max_length=500)
    budget: int = Field(ge=0)


class LeadUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    company: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    employees: int | None = Field(
        default=None,
        ge=0
    )

    need: str | None = Field(
        default=None,
        min_length=1,
        max_length=500
    )

    budget: int | None = Field(
        default=None,
        ge=0
    )


# -------------------------
# Database Dependency
# -------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -------------------------
# Business Logic
# -------------------------

def calculate_score(lead_data):
    score = 0

    # Budget score
    if lead_data["budget"] >= 5000:
        score += 50
    elif lead_data["budget"] >= 2000:
        score += 30
    elif lead_data["budget"] >= 1000:
        score += 15

    # Company size score
    if lead_data["employees"] >= 100:
        score += 30
    elif lead_data["employees"] >= 20:
        score += 20
    elif lead_data["employees"] >= 5:
        score += 10

    # AI interest score
    if "AI" in lead_data["need"].upper():
        score += 20

    return score


def get_status(score):
    if score >= 70:
        return "Hot Lead"

    if score >= 40:
        return "Warm Lead"

    return "Cold Lead"


# -------------------------
# Health
# -------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


# -------------------------
# Get All Leads
# -------------------------

@app.get("/leads")
def get_all_leads(
    db: Session = Depends(get_db)
):
    return db.query(Lead).all()


# -------------------------
# Create Lead
# -------------------------

@app.post("/leads", status_code=201)
def create_lead(
    lead: LeadCreate,
    db: Session = Depends(get_db)
):
    lead_data = lead.model_dump()

    score = calculate_score(lead_data)
    status = get_status(score)

    new_lead = Lead(
        name=lead.name,
        company=lead.company,
        employees=lead.employees,
        need=lead.need,
        budget=lead.budget,
        score=score,
        status=status
    )

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    return new_lead


# -------------------------
# Get One Lead
# -------------------------

@app.get("/leads/{lead_id}")
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id)
        .first()
    )

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    return lead


# -------------------------
# Update Lead
# -------------------------

@app.patch("/leads/{lead_id}")
def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db)
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id)
        .first()
    )

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    update_data = lead_update.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    if any(value is None for value in update_data.values()):
        raise HTTPException(
            status_code=422,
            detail="Fields cannot be null"
        )

    for field, value in update_data.items():
        setattr(lead, field, value)

    lead_data = {
        "name": lead.name,
        "company": lead.company,
        "employees": lead.employees,
        "need": lead.need,
        "budget": lead.budget
    }

    lead.score = calculate_score(lead_data)
    lead.status = get_status(lead.score)

    db.commit()
    db.refresh(lead)

    return lead


# -------------------------
# Delete Lead
# -------------------------

@app.delete("/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id)
        .first()
    )

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found"
        )

    db.delete(lead)
    db.commit()

    return {
        "message": "Lead deleted successfully",
        "id": lead_id
    }