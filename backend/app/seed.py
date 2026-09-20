import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers.local import LocalAIProvider
from app.core.config import settings
from app.core.enums import ActivityType, PipelineStage, TaskPriority, TaskStatus
from app.db.session import SessionLocal
from app.models.lead import Lead
from app.models.task import SalesTask
from app.services.activity import create_activity
from app.services.scoring import score_lead
from app.services.intelligence import SalesIntelligenceService

DEMO_LEADS = [
    {
        "name": "Michael Brown",
        "company": "OrbitFlow SaaS",
        "employees": 85,
        "need": "AI-assisted lead qualification for the sales team",
        "budget": 9000,
        "pipeline_stage": PipelineStage.QUALIFIED,
        "activity": (ActivityType.MEETING, "Discovery meeting completed with VP of Sales"),
        "task": ("Prepare workflow proposal", 2, TaskPriority.HIGH, TaskStatus.PENDING),
    },
    {
        "name": "Sarah Mitchell",
        "company": "Stonebridge Construction",
        "employees": 140,
        "need": "Centralize incoming project inquiries and follow-ups",
        "budget": 3500,
        "pipeline_stage": PipelineStage.CONTACTED,
        "activity": (ActivityType.CALL, "Discussed regional sales process and response times"),
        "task": ("Send case study", -1, TaskPriority.HIGH, TaskStatus.PENDING),
    },
    {
        "name": "Daniel Kim",
        "company": "Northstar Digital",
        "employees": 12,
        "need": "Improve agency lead tracking",
        "budget": 800,
        "pipeline_stage": PipelineStage.NEW,
        "activity": (ActivityType.NOTE, "Inbound lead from portfolio contact form"),
        "task": ("Qualify agency requirements", 4, TaskPriority.MEDIUM, TaskStatus.PENDING),
    },
    {
        "name": "Elena Garcia",
        "company": "Cartloom Commerce",
        "employees": 55,
        "need": "AI sales follow-up for high-value shopping enquiries",
        "budget": 7000,
        "pipeline_stage": PipelineStage.PROPOSAL,
        "activity": (ActivityType.EMAIL, "Proposal shared with commercial director"),
        "task": ("Review proposal feedback", 1, TaskPriority.HIGH, TaskStatus.PENDING),
    },
    {
        "name": "Noah Williams",
        "company": "ApexByte Consulting",
        "employees": 32,
        "need": "AI qualification platform for consulting opportunities",
        "budget": 5200,
        "pipeline_stage": PipelineStage.WON,
        "activity": (ActivityType.MEETING, "Commercial terms accepted"),
        "task": ("Handoff to implementation", -3, TaskPriority.MEDIUM, TaskStatus.COMPLETED),
    },
    {
        "name": "Priya Shah",
        "company": "ForgeWorks Manufacturing",
        "employees": 220,
        "need": "Distributor enquiry management",
        "budget": 1800,
        "pipeline_stage": PipelineStage.LOST,
        "activity": (ActivityType.NOTE, "Project deferred until the next budget cycle"),
        "task": ("Revisit next quarter", 60, TaskPriority.LOW, TaskStatus.CANCELLED),
    },
]


def seed_demo_data(
    db: Session, *, reset: bool = False, demo_mode: bool = False
) -> dict[str, int]:
    companies = [item["company"] for item in DEMO_LEADS]
    existing = list(db.scalars(select(Lead).where(Lead.company.in_(companies))).all())
    if reset:
        if not demo_mode:
            raise RuntimeError("Demo reset requires DEMO_MODE=true")
        for lead in db.scalars(select(Lead)).all():
            db.delete(lead)
        db.flush()
        existing = []

    existing_companies = {lead.company for lead in existing}
    created = 0
    now = datetime.now(timezone.utc)
    for item in DEMO_LEADS:
        if item["company"] in existing_companies:
            continue
        result = score_lead(item["budget"], item["employees"], item["need"])
        lead = Lead(
            name=item["name"],
            company=item["company"],
            employees=item["employees"],
            need=item["need"],
            budget=item["budget"],
            score=result.score,
            status=result.status,
            score_reasons=result.reasons,
            pipeline_stage=item["pipeline_stage"],
        )
        db.add(lead)
        db.flush()
        create_activity(
            db,
            lead_id=lead.id,
            activity_type=ActivityType.LEAD_CREATED,
            description=f"Demo lead created for {lead.name} at {lead.company}",
            metadata={"source": "demo_seed"},
        )
        if lead.pipeline_stage != PipelineStage.NEW:
            create_activity(
                db,
                lead_id=lead.id,
                activity_type=ActivityType.STAGE_CHANGED,
                description=f"Pipeline stage changed from New to {lead.pipeline_stage.value}",
                metadata={"from": "New", "to": lead.pipeline_stage.value},
            )
        activity_type, activity_description = item["activity"]
        create_activity(
            db,
            lead_id=lead.id,
            activity_type=activity_type,
            description=activity_description,
            metadata={"source": "demo_seed"},
        )
        title, due_offset, priority, task_state = item["task"]
        completed_at = now if task_state == TaskStatus.COMPLETED else None
        db.add(
            SalesTask(
                lead_id=lead.id,
                title=title,
                description="Demo follow-up task for the portfolio scenario",
                due_at=now + timedelta(days=due_offset),
                status=task_state,
                priority=priority,
                completed_at=completed_at,
            )
        )
        created += 1
    db.commit()
    return {"created": created, "existing": len(DEMO_LEADS) - created}


def seed_demo_intelligence(db: Session) -> int:
    """Prepare the flagship lead with local, deterministic intelligence."""
    lead = db.scalar(select(Lead).where(Lead.company == "OrbitFlow SaaS"))
    if lead is None:
        raise RuntimeError("Seed demo data before generating demo intelligence")
    SalesIntelligenceService(LocalAIProvider()).generate_for_lead(db, lead)
    db.commit()
    return lead.id


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed realistic SalesOps AI demo data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Replace only the six known demo companies; other records are preserved",
    )
    parser.add_argument(
        "--with-intelligence",
        action="store_true",
        help="Generate deterministic local intelligence for OrbitFlow SaaS",
    )
    args = parser.parse_args()
    if args.reset and not settings.demo_mode:
        parser.error("--reset requires DEMO_MODE=true")
    with SessionLocal() as db:
        result = seed_demo_data(db, reset=args.reset, demo_mode=settings.demo_mode)
        intelligence_lead_id = seed_demo_intelligence(db) if args.with_intelligence else None
    print(f"Demo data ready: {result['created']} created, {result['existing']} already existed")
    if intelligence_lead_id is not None:
        print(f"Local intelligence ready for lead id={intelligence_lead_id}")


if __name__ == "__main__":
    main()
