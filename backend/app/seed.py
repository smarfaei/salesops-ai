import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai.providers.local import LocalAIProvider
from app.core.config import settings
from app.core.enums import ActivityType, PipelineStage, TaskPriority, TaskStatus, UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.lead import Lead
from app.models.audit import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.task import SalesTask
from app.models.user import User
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

DEMO_USERS = [
    ("admin@salesops.demo", "Avery Admin", UserRole.ADMIN),
    ("manager@salesops.demo", "Morgan Manager", UserRole.SALES_MANAGER),
    ("rep@salesops.demo", "Riley Representative", UserRole.SALES_REP),
    ("viewer@salesops.demo", "Valerie Viewer", UserRole.VIEWER),
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


def seed_demo_users(
    db: Session, *, demo_mode: bool, password: str, reset: bool = False
) -> dict[str, int]:
    if not demo_mode:
        raise RuntimeError("Demo account seeding requires DEMO_MODE=true")
    if reset:
        db.execute(delete(AuditLog))
        db.execute(delete(RefreshToken))
        db.execute(delete(User))
        db.flush()
    created = 0
    users: dict[str, User] = {}
    for email, full_name, role in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, full_name=full_name, role=role, is_active=True)
            db.add(user)
            created += 1
        user.full_name = full_name
        user.role = role
        user.is_active = True
        user.hashed_password = hash_password(password)
        users[email] = user
    db.flush()
    rep = users["rep@salesops.demo"]
    for lead in db.scalars(select(Lead)).all():
        lead.owner_user_id = rep.id
    db.commit()
    return {"created": created, "existing": len(DEMO_USERS) - created}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed realistic SalesOps AI demo data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Replace the dedicated demo database with its canonical fictional dataset",
    )
    parser.add_argument(
        "--with-intelligence",
        action="store_true",
        help="Generate deterministic local intelligence for OrbitFlow SaaS",
    )
    parser.add_argument(
        "--with-users",
        action="store_true",
        help="Create demo RBAC accounts and assign demo leads",
    )
    args = parser.parse_args()
    if args.reset and not settings.demo_mode:
        parser.error("--reset requires DEMO_MODE=true")
    if args.with_users and not settings.demo_mode:
        parser.error("--with-users requires DEMO_MODE=true")
    if args.with_users and settings.demo_account_password is None:
        parser.error("--with-users requires DEMO_ACCOUNT_PASSWORD")
    with SessionLocal() as db:
        result = seed_demo_data(db, reset=args.reset, demo_mode=settings.demo_mode)
        intelligence_lead_id = seed_demo_intelligence(db) if args.with_intelligence else None
        user_result = (
            seed_demo_users(
                db,
                demo_mode=settings.demo_mode,
                password=settings.demo_account_password.get_secret_value(),
                reset=args.reset,
            )
            if args.with_users and settings.demo_account_password
            else None
        )
    print(f"Demo data ready: {result['created']} created, {result['existing']} already existed")
    if intelligence_lead_id is not None:
        print(f"Local intelligence ready for lead id={intelligence_lead_id}")
    if user_result is not None:
        print(
            f"Demo users ready: {user_result['created']} created, "
            f"{user_result['existing']} already existed"
        )


if __name__ == "__main__":
    main()
