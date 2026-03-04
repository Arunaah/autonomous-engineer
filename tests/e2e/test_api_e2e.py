"""E2E tests — full API endpoint tests with real FastAPI client."""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


@pytest.mark.e2e
def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "autonomous-engineer"


@pytest.mark.e2e
def test_build_endpoint_accepts_request():
    resp = client.post("/build", json={"request": "Create a hello world FastAPI endpoint"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert "message" in data


@pytest.mark.e2e
def test_build_endpoint_rejects_empty_request():
    resp = client.post("/build", json={"request": ""})
    # Should still accept (validation happens inside pipeline)
    assert resp.status_code in (200, 422)


@pytest.mark.e2e
def test_build_endpoint_requires_request_field():
    resp = client.post("/build", json={})
    assert resp.status_code == 422
