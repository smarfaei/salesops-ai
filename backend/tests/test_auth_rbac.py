from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import AuditEventType, PipelineStage, UserRole
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.main import create_app
from app.models.audit import AuditLog
from app.models.lead import Lead
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.seed import seed_demo_data, seed_demo_users
from app.services.audit import record_audit

PASSWORD = "PortfolioDemo!123"


def auth_settings(*, demo_mode: bool = False, login_limit: int = 100) -> Settings:
    return Settings(
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        CORS_ORIGINS="http://localhost:3000",
        JWT_SECRET="test-only-jwt-secret-at-least-32-characters",
        DEMO_MODE=demo_mode,
        LOGIN_RATE_LIMIT_REQUESTS=login_limit,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=60,
        _env_file=None,
    )


@contextmanager
def auth_client(
    db_session: Session, *, settings: Settings | None = None
) -> Generator[tuple[TestClient, Settings], None, None]:
    active = settings or auth_settings()
    app = create_app(active)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, active


def add_user(
    db: Session,
    email: str,
    role: UserRole,
    *,
    active: bool = True,
    password: str = PASSWORD,
) -> User:
    user = User(
        email=email.lower(),
        full_name=email.split("@")[0].replace(".", " ").title(),
        hashed_password=hash_password(password),
        role=role,
        is_active=active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def headers(user: User, settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, settings)}"}


def add_lead(db: Session, *, owner: User | None = None) -> Lead:
    lead = Lead(
        name="Assigned Lead",
        company="Fictional Labs",
        employees=25,
        need="Sales automation",
        budget=3000,
        score=40,
        status="Warm",
        score_reasons=["Mid-range budget: +30", "Growing company: +10"],
        pipeline_stage=PipelineStage.NEW,
        owner_user_id=owner.id if owner else None,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def test_password_hashing_is_salted_and_never_plaintext():
    first = hash_password(PASSWORD)
    second = hash_password(PASSWORD)
    assert first != second
    assert PASSWORD not in first
    assert verify_password(PASSWORD, first)
    assert not verify_password("WrongPassword!", first)


def test_login_me_refresh_rotation_and_logout(db_session: Session):
    user = add_user(db_session, "admin@example.com", UserRole.ADMIN)
    with auth_client(db_session) as (client, _):
        login = client.post("/auth/login", json={"email": "ADMIN@EXAMPLE.COM", "password": PASSWORD})
        assert login.status_code == 200
        token = login.json()["access_token"]
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["id"] == user.id
        first_refresh = client.cookies.get("salesops_refresh")
        refreshed = client.post("/auth/refresh")
        assert refreshed.status_code == 200
        assert refreshed.json()["access_token"] != token
        assert client.cookies.get("salesops_refresh") != first_refresh
        old_record = db_session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash.is_not(None)).order_by(RefreshToken.id)
        )
        assert old_record is not None and old_record.revoked_at is not None
        assert client.post("/auth/logout").status_code == 204
        assert client.post("/auth/refresh").status_code == 401


def test_login_failure_inactive_user_and_rate_limit(db_session: Session):
    add_user(db_session, "inactive@example.com", UserRole.VIEWER, active=False)
    with auth_client(db_session, settings=auth_settings(login_limit=2)) as (client, _):
        missing = client.post("/auth/login", json={"email": "missing@example.com", "password": PASSWORD})
        inactive = client.post("/auth/login", json={"email": "inactive@example.com", "password": PASSWORD})
        limited = client.post("/auth/login", json={"email": "missing@example.com", "password": PASSWORD})
        assert missing.status_code == inactive.status_code == 401
        assert missing.json()["error"]["message"] == inactive.json()["error"]["message"]
        assert limited.status_code == 429


def test_invalid_and_expired_access_tokens(db_session: Session):
    user = add_user(db_session, "viewer@example.com", UserRole.VIEWER)
    settings = auth_settings()
    expired = create_access_token(user.id, settings, now=datetime.now(timezone.utc) - timedelta(hours=1))
    with auth_client(db_session, settings=settings) as (client, _):
        assert client.get("/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
        assert client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_admin_user_management_hashes_password_and_audits(db_session: Session):
    admin = add_user(db_session, "admin@example.com", UserRole.ADMIN)
    with auth_client(db_session) as (client, settings):
        created = client.post(
            "/users",
            headers=headers(admin, settings),
            json={
                "email": "NEW.REP@EXAMPLE.COM",
                "full_name": "New Representative",
                "password": PASSWORD,
                "role": "sales_rep",
            },
        )
        assert created.status_code == 201
        assert "hashed_password" not in created.json()
        stored = db_session.scalar(select(User).where(User.email == "new.rep@example.com"))
        assert stored is not None and verify_password(PASSWORD, stored.hashed_password)
        changed = client.patch(
            f"/users/{stored.id}",
            headers=headers(admin, settings),
            json={"role": "viewer", "is_active": False},
        )
        assert changed.status_code == 200
        events = set(db_session.scalars(select(AuditLog.event_type)).all())
        assert {
            AuditEventType.USER_CREATED,
            AuditEventType.ROLE_CHANGED,
            AuditEventType.USER_DEACTIVATED,
        }.issubset(events)


def test_role_permissions_ownership_and_reassignment(db_session: Session):
    admin = add_user(db_session, "admin@example.com", UserRole.ADMIN)
    manager = add_user(db_session, "manager@example.com", UserRole.SALES_MANAGER)
    rep = add_user(db_session, "rep@example.com", UserRole.SALES_REP)
    other_rep = add_user(db_session, "other.rep@example.com", UserRole.SALES_REP)
    viewer = add_user(db_session, "viewer@example.com", UserRole.VIEWER)
    lead = add_lead(db_session, owner=rep)
    with auth_client(db_session) as (client, settings):
        assert client.get(f"/leads/{lead.id}", headers=headers(rep, settings)).status_code == 200
        assert client.get(f"/leads/{lead.id}", headers=headers(other_rep, settings)).status_code == 403
        assert client.get(f"/leads/{lead.id}", headers=headers(viewer, settings)).status_code == 200
        assert client.patch(
            f"/leads/{lead.id}/stage",
            headers=headers(viewer, settings),
            json={"stage": "Qualified"},
        ).status_code == 403
        assert client.get("/users", headers=headers(manager, settings)).status_code == 403
        assigned = client.patch(
            f"/leads/{lead.id}/owner",
            headers=headers(manager, settings),
            json={"owner_user_id": other_rep.id},
        )
        assert assigned.status_code == 200
        assert assigned.json()["owner_user_id"] == other_rep.id
        assert client.get(f"/leads/{lead.id}", headers=headers(other_rep, settings)).status_code == 200
        assert client.get("/users", headers=headers(admin, settings)).status_code == 200


def test_audit_log_authorization(db_session: Session):
    manager = add_user(db_session, "manager@example.com", UserRole.SALES_MANAGER)
    rep = add_user(db_session, "rep@example.com", UserRole.SALES_REP)
    lead = add_lead(db_session, owner=rep)
    with auth_client(db_session) as (client, settings):
        moved = client.patch(
            f"/leads/{lead.id}/stage",
            headers=headers(rep, settings),
            json={"stage": "Qualified"},
        )
        assert moved.status_code == 200
        assert client.get("/audit-logs", headers=headers(rep, settings)).status_code == 403
        audit = client.get("/audit-logs", headers=headers(manager, settings))
        assert audit.status_code == 200
        assert audit.json()["items"][0]["event_type"] == "pipeline_changed"


def test_audit_metadata_recursively_removes_sensitive_values(db_session: Session):
    event = record_audit(
        db_session,
        actor_user_id=None,
        event_type=AuditEventType.LEAD_UPDATED,
        entity_type="lead",
        entity_id=1,
        metadata={
            "safe": "retained",
            "new_password": "must-not-be-retained",
            "nested": {"authorization_header": "must-not-be-retained", "field": "retained"},
        },
    )
    db_session.commit()
    db_session.refresh(event)
    assert event.audit_metadata == {"safe": "retained", "nested": {"field": "retained"}}


def test_demo_accounts_and_demo_mode_precedence(db_session: Session):
    seed_demo_data(db_session)
    result = seed_demo_users(db_session, demo_mode=True, password=PASSWORD)
    assert result["created"] == 4
    admin = db_session.scalar(select(User).where(User.email == "admin@salesops.demo"))
    lead = db_session.scalar(select(Lead).where(Lead.company == "OrbitFlow SaaS"))
    assert admin is not None and lead is not None and lead.owner_user_id is not None
    settings = auth_settings(demo_mode=True)
    with auth_client(db_session, settings=settings) as (client, _):
        forbidden = client.delete(f"/leads/{lead.id}", headers=headers(admin, settings))
        assert forbidden.status_code == 403


def test_demo_account_seed_refuses_non_demo_and_reset_is_idempotent(db_session: Session):
    try:
        seed_demo_users(db_session, demo_mode=False, password=PASSWORD)
    except RuntimeError as exc:
        assert "DEMO_MODE=true" in str(exc)
    else:
        raise AssertionError("Demo account seed must refuse non-demo environments")

    seed_demo_data(db_session, reset=True, demo_mode=True)
    first = seed_demo_users(db_session, demo_mode=True, password=PASSWORD, reset=True)
    second = seed_demo_users(db_session, demo_mode=True, password=PASSWORD, reset=True)
    assert first["created"] == second["created"] == 4
    assert len(db_session.scalars(select(User)).all()) == 4
    assert all(lead.owner_user_id is not None for lead in db_session.scalars(select(Lead)).all())
