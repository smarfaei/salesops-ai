import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.factory import create_ai_provider
from app.ai.providers.base import AIProvider, AIProviderError, MalformedProviderResponse
from app.ai.providers.local import LocalAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import Settings
from app.core.enums import PipelineStage
from app.main import app
from app.models.lead import Lead
from app.schemas.intelligence import (
    ActivityContext,
    IntelligenceContext,
    SalesIntelligence,
    TaskContext,
)
from app.seed import seed_demo_data
from app.services.intelligence import SalesIntelligenceService, get_sales_intelligence_service


def make_context(**overrides) -> IntelligenceContext:
    now = datetime.now(timezone.utc)
    values = {
        "lead_id": 1,
        "name": "Michael Brown",
        "company": "Acme Technologies",
        "employees": 80,
        "need": "AI lead qualification automation",
        "budget": 7000,
        "score": 90,
        "qualification_status": "Hot",
        "pipeline_stage": PipelineStage.QUALIFIED,
        "recent_activities": [
            ActivityContext(type="meeting", description="Discovery meeting", created_at=now)
        ],
        "open_tasks": [],
        "generated_at": now,
    }
    return IntelligenceContext(**{**values, **overrides})


def create_lead(client: TestClient, **overrides) -> dict:
    payload = {
        "name": "Michael Brown",
        "company": "Acme Technologies",
        "employees": 80,
        "need": "AI lead qualification automation",
        "budget": 7000,
        **overrides,
    }
    response = client.post("/leads", json=payload)
    assert response.status_code == 201
    return response.json()


def test_local_provider_returns_deterministic_structured_intelligence():
    provider = LocalAIProvider()
    context = make_context()
    first = provider.generate(context)
    second = provider.generate(context)
    assert first == second
    assert "Acme Technologies" in first.qualification_summary
    assert first.next_best_action.action == "Schedule discovery call"
    assert first.follow_up.subject == "Next steps for Acme Technologies"
    assert "Michael" in first.follow_up.message


def test_local_provider_derives_buying_and_risk_signals_from_facts():
    provider = LocalAIProvider()
    strong = provider.generate(make_context())
    assert {item.signal for item in strong.buying_signals} >= {
        "High budget",
        "Established company",
        "AI or automation requirement",
        "High lead score",
    }

    weak = provider.generate(
        make_context(
            employees=2,
            need="Website",
            budget=300,
            score=0,
            qualification_status="Cold",
            pipeline_stage=PipelineStage.NEW,
            recent_activities=[],
        )
    )
    risks = {item.signal for item in weak.risks}
    assert risks >= {"Low budget", "Very small company", "Low qualification score", "Requirement needs clarification", "No recent sales activity"}
    assert weak.next_best_action.action == "Nurture lead"


def test_overdue_task_takes_priority():
    now = datetime.now(timezone.utc)
    result = LocalAIProvider().generate(
        make_context(
            open_tasks=[
                TaskContext(
                    title="Call customer",
                    status="pending",
                    priority="high",
                    due_at=now - timedelta(days=1),
                )
            ],
            generated_at=now,
        )
    )
    assert result.next_best_action.action == "Resolve overdue task"
    assert result.next_best_action.priority.value == "high"
    assert any(item.signal == "Overdue follow-up" for item in result.risks)


def test_openai_provider_uses_structured_output_without_network():
    expected = LocalAIProvider().generate(make_context())
    captured = {}

    def transport(payload: dict, timeout: float) -> dict:
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": expected.model_dump_json()}]}
            ]
        }

    provider = OpenAIProvider(api_key="test-key", model="test-model", timeout_seconds=7, transport=transport)
    result = provider.generate(make_context())
    assert result == expected
    assert captured["timeout"] == 7
    assert captured["payload"]["store"] is False
    assert captured["payload"]["text"]["format"]["type"] == "json_schema"
    assert captured["payload"]["text"]["format"]["strict"] is True
    assert "test-key" not in json.dumps(captured["payload"])


def test_openai_provider_rejects_malformed_response_and_handles_timeout():
    malformed = OpenAIProvider(
        api_key="test-key",
        model="test-model",
        transport=lambda _payload, _timeout: {"output_text": '{"qualification_summary": "incomplete"}'},
    )
    with pytest.raises(MalformedProviderResponse):
        malformed.generate(make_context())

    def timeout_transport(_payload, _timeout):
        raise TimeoutError

    timed_out = OpenAIProvider(
        api_key="test-key", model="test-model", transport=timeout_transport
    )
    with pytest.raises(AIProviderError, match="timed out"):
        timed_out.generate(make_context())


def test_structured_schema_validation_rejects_arbitrary_output():
    with pytest.raises(ValidationError):
        SalesIntelligence.model_validate(
            {
                "qualification_summary": "Summary",
                "buying_signals": [],
                "risks": [],
                "next_best_action": {"action": "Call", "reason": "Relevant", "priority": "high"},
                "follow_up": {"subject": "Hello", "message": "Message"},
                "unexpected": "not allowed",
            }
        )


def test_provider_selection():
    local_settings = Settings(
        DATABASE_URL="sqlite+pysqlite:///:memory:", AI_PROVIDER="local", _env_file=None
    )
    assert isinstance(create_ai_provider(local_settings), LocalAIProvider)
    openai_settings = Settings(
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AI_PROVIDER="openai",
        OPENAI_API_KEY="secret",
        OPENAI_MODEL="test-model",
        _env_file=None,
    )
    provider = create_ai_provider(openai_settings)
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "test-model"


def test_intelligence_api_generation_get_and_regeneration(client: TestClient):
    lead = create_lead(client)
    first = client.post(f"/leads/{lead['id']}/intelligence")
    assert first.status_code == 200
    body = first.json()
    assert body["provider"] == "local"
    assert body["next_best_action"]["action"] == "Contact immediately"
    retrieved = client.get(f"/leads/{lead['id']}/intelligence")
    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == body["id"]

    client.patch(f"/leads/{lead['id']}/stage", json={"stage": "Qualified"})
    regenerated = client.post(f"/leads/{lead['id']}/intelligence")
    assert regenerated.status_code == 200
    assert regenerated.json()["id"] == body["id"]
    assert regenerated.json()["next_best_action"]["action"] == "Schedule discovery call"
    activities = client.get(f"/leads/{lead['id']}/activities").json()
    generated_events = [
        item for item in activities
        if item.get("metadata", {}).get("event") == "sales_intelligence_generated"
    ]
    assert len(generated_events) == 1


def test_intelligence_api_errors(client: TestClient):
    assert client.post("/leads/999/intelligence").status_code == 404
    assert client.get("/leads/999/intelligence").status_code == 404
    lead = create_lead(client)
    missing = client.get(f"/leads/{lead['id']}/intelligence")
    assert missing.status_code == 404
    assert missing.json()["error"]["message"] == "Sales intelligence has not been generated"


class FailingProvider(AIProvider):
    name = "failing"
    model = "failure-test"

    def generate(self, context: IntelligenceContext) -> SalesIntelligence:
        raise AIProviderError("simulated failure")


def test_provider_failure_falls_back_to_local(client: TestClient):
    service = SalesIntelligenceService(FailingProvider(), fallback_provider=LocalAIProvider())
    app.dependency_overrides[get_sales_intelligence_service] = lambda: service
    lead = create_lead(client)
    response = client.post(f"/leads/{lead['id']}/intelligence")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["provider_metadata"] == {
        "fallback_from": "failing",
        "reason": "AIProviderError",
    }


def test_provider_failure_without_fallback_returns_503(client: TestClient):
    app.dependency_overrides[get_sales_intelligence_service] = lambda: SalesIntelligenceService(
        FailingProvider()
    )
    lead = create_lead(client)
    response = client.post(f"/leads/{lead['id']}/intelligence")
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "Sales intelligence provider is unavailable"


def test_demo_leads_produce_diverse_recommendations(client: TestClient, db_session: Session):
    seed_demo_data(db_session)
    leads = {
        lead.company: lead for lead in db_session.scalars(select(Lead)).all()
    }
    expected = {
        "OrbitFlow SaaS": "Schedule discovery call",
        "Stonebridge Construction": "Resolve overdue task",
        "Northstar Digital": "Nurture lead",
    }
    for company, action in expected.items():
        response = client.post(f"/leads/{leads[company].id}/intelligence")
        assert response.status_code == 200
        assert response.json()["next_best_action"]["action"] == action
