from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def create_lead(client: TestClient, **overrides):
    payload = {
        "name": "Michael Brown",
        "company": "Acme Technologies",
        "employees": 45,
        "need": "AI lead qualification",
        "budget": 5000,
        **overrides,
    }
    response = client.post("/leads", json=payload)
    assert response.status_code == 201
    return response.json()


def task_payload(*, days: int = 2, priority: str = "medium") -> dict:
    return {
        "title": "Discovery call",
        "description": "Confirm qualification requirements",
        "due_at": (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(),
        "priority": priority,
    }


def test_new_lead_defaults_to_new_and_creates_activity(client: TestClient):
    lead = create_lead(client)
    assert lead["pipeline_stage"] == "New"
    activities = client.get(f"/leads/{lead['id']}/activities").json()
    assert len(activities) == 1
    assert activities[0]["type"] == "lead_created"


def test_valid_stage_transition_creates_history(client: TestClient):
    lead = create_lead(client)
    response = client.patch(f"/leads/{lead['id']}/stage", json={"stage": "Qualified"})
    assert response.status_code == 200
    assert response.json()["pipeline_stage"] == "Qualified"
    activities = client.get(f"/leads/{lead['id']}/activities").json()
    stage_activity = next(item for item in activities if item["type"] == "stage_changed")
    assert stage_activity["metadata"] == {"from": "New", "to": "Qualified"}


def test_invalid_and_duplicate_stage_are_rejected(client: TestClient):
    lead = create_lead(client)
    invalid = client.patch(f"/leads/{lead['id']}/stage", json={"stage": "Negotiating"})
    assert invalid.status_code == 422
    duplicate = client.patch(f"/leads/{lead['id']}/stage", json={"stage": "New"})
    assert duplicate.status_code == 409
    activities = client.get(f"/leads/{lead['id']}/activities").json()
    assert [item["type"] for item in activities] == ["lead_created"]


def test_manual_activity_creation_listing_and_retrieval(client: TestClient):
    lead = create_lead(client)
    response = client.post(
        f"/leads/{lead['id']}/activities",
        json={"type": "note", "description": "Decision maker confirmed", "metadata": {"channel": "CRM"}},
    )
    assert response.status_code == 201
    activity = response.json()
    assert activity["type"] == "note"
    assert client.get(f"/activities/{activity['id']}").json()["description"] == "Decision maker confirmed"
    assert len(client.get(f"/leads/{lead['id']}/activities").json()) == 2


def test_automatic_update_activity_is_not_noisy(client: TestClient):
    lead = create_lead(client)
    changed = client.patch(f"/leads/{lead['id']}", json={"budget": 6000})
    assert changed.status_code == 200
    unchanged = client.patch(f"/leads/{lead['id']}", json={"budget": 6000})
    assert unchanged.status_code == 200
    activities = client.get(f"/leads/{lead['id']}/activities").json()
    assert [item["type"] for item in activities].count("lead_updated") == 1


def test_task_creation_update_and_get(client: TestClient):
    lead = create_lead(client)
    created = client.post(f"/leads/{lead['id']}/tasks", json=task_payload())
    assert created.status_code == 201
    task = created.json()
    assert task["status"] == "pending"
    updated = client.patch(
        f"/tasks/{task['id']}", json={"title": "Technical discovery", "priority": "high"}
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Technical discovery"
    assert client.get(f"/tasks/{task['id']}").json()["priority"] == "high"


def test_task_completion_and_cancellation_timestamps(client: TestClient):
    lead = create_lead(client)
    task = client.post(f"/leads/{lead['id']}/tasks", json=task_payload()).json()
    completed = client.post(f"/tasks/{task['id']}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["completed_at"] is not None
    cancelled = client.post(f"/tasks/{task['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["completed_at"] is None


def test_task_filters_overdue_upcoming_and_priority(client: TestClient):
    lead = create_lead(client)
    client.post(f"/leads/{lead['id']}/tasks", json=task_payload(days=-2, priority="high"))
    client.post(
        f"/leads/{lead['id']}/tasks",
        json={**task_payload(days=3, priority="low"), "title": "Future follow-up"},
    )
    overdue = client.get("/tasks", params={"timing": "overdue"}).json()
    upcoming = client.get("/tasks", params={"timing": "upcoming"}).json()
    high = client.get("/tasks", params={"priority": "high"}).json()
    assert overdue["total"] == 1
    assert upcoming["total"] == 1
    assert high["total"] == 1
    assert high["items"][0]["priority"] == "high"


def test_task_validation_and_not_found(client: TestClient):
    lead = create_lead(client)
    naive_due = datetime.now().replace(microsecond=0).isoformat()
    assert client.post(
        f"/leads/{lead['id']}/tasks", json={**task_payload(), "due_at": naive_due}
    ).status_code == 422
    assert client.post(
        f"/leads/{lead['id']}/tasks", json={**task_payload(), "priority": "urgent"}
    ).status_code == 422
    task = client.post(f"/leads/{lead['id']}/tasks", json=task_payload()).json()
    assert client.patch(f"/tasks/{task['id']}", json={"status": "snoozed"}).status_code == 422
    assert client.get("/tasks/999").status_code == 404


def test_task_deletion(client: TestClient):
    lead = create_lead(client)
    task = client.post(f"/leads/{lead['id']}/tasks", json=task_payload()).json()
    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_lead_detail_contains_timeline_and_upcoming_tasks(client: TestClient):
    lead = create_lead(client)
    client.post(f"/leads/{lead['id']}/activities", json={"type": "call", "description": "Intro call"})
    client.post(f"/leads/{lead['id']}/tasks", json=task_payload(days=2))
    detail = client.get(f"/leads/{lead['id']}/detail")
    assert detail.status_code == 200
    body = detail.json()
    assert body["lead"]["id"] == lead["id"]
    assert len(body["recent_activities"]) == 2
    assert len(body["upcoming_tasks"]) == 1


def test_pipeline_and_score_range_filters(client: TestClient):
    cold = create_lead(
        client, name="Cold Lead", company="Small Co", employees=1, need="Website", budget=100
    )
    hot = create_lead(
        client, name="Hot Lead", company="Large Co", employees=100, need="AI", budget=5000
    )
    client.patch(f"/leads/{hot['id']}/stage", json={"stage": "Qualified"})
    result = client.get(
        "/leads", params={"pipeline_stage": "Qualified", "min_score": 70, "max_score": 100}
    )
    assert result.status_code == 200
    assert result.json()["total"] == 1
    assert result.json()["items"][0]["id"] == hot["id"]
    assert client.get("/leads", params={"min_score": 80, "max_score": 20}).status_code == 422
    assert cold["pipeline_stage"] == "New"


def test_deleting_lead_cascades_workflow_records(client: TestClient):
    lead = create_lead(client)
    task = client.post(f"/leads/{lead['id']}/tasks", json=task_payload()).json()
    activity = client.post(
        f"/leads/{lead['id']}/activities", json={"type": "note", "description": "Temporary"}
    ).json()
    assert client.delete(f"/leads/{lead['id']}").status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404
    assert client.get(f"/activities/{activity['id']}").status_code == 404
