from fastapi.testclient import TestClient


VALID_LEAD = {
    "name": "Alex Morgan",
    "company": "NovaTech",
    "employees": 60,
    "need": "AI sales assistant",
    "budget": 7000,
}


def create_lead(client: TestClient, **overrides):
    payload = {**VALID_LEAD, **overrides}
    response = client.post("/leads", json=payload)
    assert response.status_code == 201
    return response.json()


def test_health_checks_database(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_create_lead_returns_scoring_explanation(client: TestClient):
    lead = create_lead(client)
    assert lead["id"] > 0
    assert lead["score"] == 90
    assert lead["status"] == "Hot"
    assert "High budget: +50" in lead["score_reasons"]
    assert lead["created_at"]


def test_create_lead_rejects_invalid_payload(client: TestClient):
    response = client.post("/leads", json={**VALID_LEAD, "name": "   ", "budget": -1})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert len(body["error"]["details"]) == 2


def test_update_recalculates_score(client: TestClient):
    lead = create_lead(client, employees=2, need="Website", budget=200)
    assert lead["score"] == 0
    response = client.patch(
        f"/leads/{lead['id']}",
        json={"employees": 150, "budget": 6000, "need": "AI qualification"},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["score"] == 100
    assert updated["status"] == "Hot"


def test_get_update_and_delete_missing_lead(client: TestClient):
    requests = [
        (client.get, {}),
        (client.patch, {"json": {"budget": 1000}}),
        (client.delete, {}),
    ]
    for method, kwargs in requests:
        response = method("/leads/999", **kwargs)
        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Lead not found"


def test_delete_lead(client: TestClient):
    lead = create_lead(client)
    response = client.delete(f"/leads/{lead['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/leads/{lead['id']}").status_code == 404


def test_listing_search_filter_sort_and_pagination(client: TestClient):
    create_lead(client, name="Cold One", company="Acme", employees=1, need="Website", budget=100)
    create_lead(client, name="Hot One", company="Nova", employees=100, need="AI", budget=5000)
    create_lead(client, name="Warm One", company="Acme Labs", employees=20, need="CRM", budget=2000)

    response = client.get(
        "/leads",
        params={"search": "acme", "status": "Warm", "sort_by": "score", "sort_order": "desc", "page": 1, "page_size": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["pages"] == 1
    assert body["items"][0]["name"] == "Warm One"


def test_list_paginates_and_sorts(client: TestClient):
    create_lead(client, name="First", budget=100, employees=1, need="Site")
    create_lead(client, name="Second", budget=5000, employees=100, need="AI")
    response = client.get("/leads", params={"sort_by": "score", "sort_order": "desc", "page_size": 1, "page": 2})
    body = response.json()
    assert body["total"] == 2
    assert body["pages"] == 2
    assert body["items"][0]["name"] == "First"
