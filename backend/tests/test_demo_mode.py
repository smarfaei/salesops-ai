from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.models.lead import Lead
from app.models.user import User
from app.seed import DEMO_LEADS, seed_demo_data


def demo_settings(*, rate_limit: int = 100) -> Settings:
    return Settings(
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        CORS_ORIGINS="https://demo.example.com",
        JWT_SECRET="test-only-jwt-secret-at-least-32-characters",
        DEMO_MODE=True,
        DEBUG=True,
        AI_PROVIDER="openai",
        OPENAI_API_KEY="must-not-be-used",
        OPENAI_MODEL="must-not-be-used",
        DEMO_RATE_LIMIT_REQUESTS=rate_limit,
        DEMO_RATE_LIMIT_WINDOW_SECONDS=60,
        _env_file=None,
    )


@contextmanager
def demo_client(db_session: Session, *, rate_limit: int = 100) -> Generator[TestClient, None, None]:
    app = create_app(demo_settings(rate_limit=rate_limit))

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    user = User(
        email="demo-admin@test.example",
        full_name="Demo Admin",
        hashed_password="not-used",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    from app.core.authz import get_current_user

    app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(app) as client:
        yield client


def test_demo_settings_force_local_ai_and_disable_debug_and_secrets():
    configured = demo_settings()
    assert configured.demo_mode is True
    assert configured.debug is False
    assert configured.ai_provider == "local"
    assert configured.openai_api_key is None
    assert configured.openai_model is None


def test_demo_settings_reject_wildcard_cors():
    with pytest.raises(ValueError, match="wildcard"):
        Settings(
            DATABASE_URL="sqlite+pysqlite:///:memory:",
            CORS_ORIGINS="*",
            JWT_SECRET="test-only-jwt-secret-at-least-32-characters",
            DEMO_MODE=True,
            _env_file=None,
        )


def test_demo_mode_hides_api_documentation(db_session: Session):
    with demo_client(db_session) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_demo_mode_blocks_destructive_lead_and_task_operations(db_session: Session):
    seed_demo_data(db_session)
    lead = db_session.scalar(select(Lead).where(Lead.company == "OrbitFlow SaaS"))
    assert lead is not None
    with demo_client(db_session) as client:
        assert client.post(
            "/leads",
            json={
                "name": "Visitor",
                "company": "Visitor Company",
                "employees": 1,
                "need": "Non-demo data",
                "budget": 1,
            },
        ).status_code == 403
        assert client.patch(f"/leads/{lead.id}", json={"budget": 1}).status_code == 403
        assert client.delete(f"/leads/{lead.id}").status_code == 403

        task = client.post(
            f"/leads/{lead.id}/tasks",
            json={
                "title": "Safe demo follow-up",
                "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "priority": "medium",
            },
        ).json()
        assert client.delete(f"/tasks/{task['id']}").status_code == 403
        assert db_session.scalar(select(func.count()).select_from(Lead)) == 6


def test_demo_mode_keeps_safe_interactions_working(db_session: Session):
    seed_demo_data(db_session)
    lead = db_session.scalar(select(Lead).where(Lead.company == "OrbitFlow SaaS"))
    assert lead is not None
    with demo_client(db_session) as client:
        stage = client.patch(f"/leads/{lead.id}/stage", json={"stage": "Contacted"})
        assert stage.status_code == 200

        activity = client.post(
            f"/leads/{lead.id}/activities",
            json={"type": "note", "description": "Public demo activity"},
        )
        assert activity.status_code == 201

        task = client.post(
            f"/leads/{lead.id}/tasks",
            json={
                "title": "Public demo task",
                "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "priority": "high",
            },
        )
        assert task.status_code == 201
        assert client.post(f"/tasks/{task.json()['id']}/complete").status_code == 200

        intelligence = client.post(f"/leads/{lead.id}/intelligence")
        assert intelligence.status_code == 200
        assert intelligence.json()["provider"] == "local"


def test_demo_reset_requires_demo_mode_and_removes_non_demo_data(db_session: Session):
    with pytest.raises(RuntimeError, match="DEMO_MODE=true"):
        seed_demo_data(db_session, reset=True, demo_mode=False)

    db_session.add(
        Lead(
            name="Real Person",
            company="Real Company",
            employees=1,
            need="Must not remain in public demo",
            budget=1,
            score=0,
            status="Cold",
            score_reasons=[],
        )
    )
    db_session.commit()
    first = seed_demo_data(db_session, reset=True, demo_mode=True)
    second = seed_demo_data(db_session, reset=True, demo_mode=True)
    companies = set(db_session.scalars(select(Lead.company)).all())

    assert first["created"] == 6
    assert second["created"] == 6
    assert companies == {item["company"] for item in DEMO_LEADS}


def test_demo_write_rate_limit_returns_429(db_session: Session):
    seed_demo_data(db_session)
    lead = db_session.scalar(select(Lead).where(Lead.company == "OrbitFlow SaaS"))
    assert lead is not None
    with demo_client(db_session, rate_limit=2) as client:
        first = client.post(
            f"/leads/{lead.id}/activities",
            json={"type": "note", "description": "First"},
        )
        second = client.post(
            f"/leads/{lead.id}/activities",
            json={"type": "note", "description": "Second"},
        )
        limited = client.post(
            f"/leads/{lead.id}/activities",
            json={"type": "note", "description": "Third"},
        )

    assert first.status_code == 201
    assert second.status_code == 201
    assert limited.status_code == 429
    assert limited.headers["Retry-After"]
    assert limited.json()["error"]["code"] == "rate_limit_exceeded"
