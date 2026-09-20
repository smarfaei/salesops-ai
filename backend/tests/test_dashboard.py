from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def test_dashboard_summary_aggregates_real_workflow_data(client: TestClient):
    hot = client.post(
        "/leads",
        json={"name": "A", "company": "OrbitFlow", "employees": 100, "need": "AI automation", "budget": 8000},
    ).json()
    client.post(
        "/leads",
        json={"name": "B", "company": "Northstar", "employees": 2, "need": "Website", "budget": 500},
    )
    client.patch(f"/leads/{hot['id']}/stage", json={"stage": "Qualified"})
    client.post(
        f"/leads/{hot['id']}/tasks",
        json={
            "title": "Follow up",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "priority": "high",
        },
    )

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["kpis"] == {
        "total_leads": 2,
        "hot_leads": 1,
        "qualified_leads": 1,
        "open_pipeline_value": 8500,
        "won_leads": 0,
        "pending_tasks": 1,
    }
    assert {item["name"]: item["value"] for item in body["pipeline_distribution"]}["Qualified"] == 1


def test_dashboard_summary_handles_empty_database(client: TestClient):
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    assert response.json()["kpis"]["total_leads"] == 0


def test_local_frontend_origin_is_allowed(client: TestClient):
    response = client.options(
        "/leads",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
