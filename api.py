import json
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel


DATA_FILE = Path("leads.json")

app = FastAPI(
    title="AI Sales Agent API",
    version="1.0.0"
)


class LeadCreate(BaseModel):
    name: str
    company: str
    employees: int
    need: str
    budget: int


def load_leads():
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_leads(leads):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            leads,
            file,
            indent=2,
            ensure_ascii=False
        )


def calculate_score(lead):
    score = 0

    if lead["budget"] >= 5000:
        score += 50
    elif lead["budget"] >= 2000:
        score += 30
    elif lead["budget"] >= 1000:
        score += 15

    if lead["employees"] >= 100:
        score += 30
    elif lead["employees"] >= 20:
        score += 20
    elif lead["employees"] >= 5:
        score += 10

    if "AI" in lead["need"].upper():
        score += 20

    return score


def get_status(score):
    if score >= 70:
        return "Hot Lead"
    elif score >= 40:
        return "Warm Lead"
    else:
        return "Cold Lead"


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/leads")
def get_all_leads():
    return load_leads()


@app.get("/leads/hot")
def get_hot_leads():
    leads = load_leads()
    hot_leads = []

    for lead in leads:
        score = lead.get("score")

        if score is None:
            score = calculate_score(lead)

        status = lead.get("status")

        if status is None:
            status = get_status(score)

        if status == "Hot Lead":
            lead["score"] = score
            lead["status"] = status
            hot_leads.append(lead)

    return hot_leads


@app.post("/leads")
def create_lead(lead: LeadCreate):
    lead_data = lead.model_dump()

    score = calculate_score(lead_data)
    status = get_status(score)

    lead_data["score"] = score
    lead_data["status"] = status

    leads = load_leads()
    leads.append(lead_data)

    save_leads(leads)

    return lead_data