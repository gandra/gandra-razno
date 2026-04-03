"""Tests for health and tools API endpoints."""


def test_health_endpoint(test_client):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "gandra-tools-api"


def test_tools_endpoint(test_client):
    response = test_client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
