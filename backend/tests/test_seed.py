from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.lead import Lead
from app.models.intelligence import LeadIntelligence
from app.models.task import SalesTask
from app.seed import seed_demo_data, seed_demo_intelligence


def test_demo_seed_is_realistic_and_idempotent(db_session: Session):
    first = seed_demo_data(db_session)
    second = seed_demo_data(db_session)
    assert first == {"created": 6, "existing": 0}
    assert second == {"created": 0, "existing": 6}
    assert db_session.scalar(select(func.count()).select_from(Lead)) == 6
    assert db_session.scalar(select(func.count()).select_from(Activity)) >= 12
    assert db_session.scalar(select(func.count()).select_from(SalesTask)) == 6
    stages = set(db_session.scalars(select(Lead.pipeline_stage)).all())
    assert len(stages) == 6
    assert set(db_session.scalars(select(Lead.status)).all()) == {"Hot", "Warm", "Cold"}
    assert len(set(db_session.scalars(select(SalesTask.status)).all())) == 3
    assert len(set(db_session.scalars(select(SalesTask.priority)).all())) == 3


def test_demo_intelligence_is_local_and_repeatable(db_session: Session):
    seed_demo_data(db_session, reset=True, demo_mode=True)
    lead_id = seed_demo_intelligence(db_session)
    second_lead_id = seed_demo_intelligence(db_session)
    records = list(db_session.scalars(select(LeadIntelligence)).all())

    assert second_lead_id == lead_id
    assert len(records) == 1
    assert records[0].lead_id == lead_id
    assert records[0].provider == "local"
