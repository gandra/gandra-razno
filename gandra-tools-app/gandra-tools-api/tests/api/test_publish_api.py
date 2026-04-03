"""Tests for publish API endpoints."""


def _get_token(client, settings) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": settings.default_user_email, "password": settings.default_user_password},
    )
    return resp.json()["access_token"]


def test_publish_requires_auth(test_client):
    response = test_client.post(
        "/api/v1/publish",
        json={"content": {}, "content_type": "generic", "format": "json"},
    )
    assert response.status_code == 401


def test_publish_json(test_client, test_settings):
    token = _get_token(test_client, test_settings)
    response = test_client.post(
        "/api/v1/publish",
        json={"content": {"title": "Test"}, "content_type": "generic", "format": "json"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "json"
    assert data["content_type_mime"] == "application/json"


def test_publish_multi(test_client, test_settings):
    token = _get_token(test_client, test_settings)
    response = test_client.post(
        "/api/v1/publish/multi",
        json={
            "content": {"summary": "Hello"},
            "content_type": "generic",
            "formats": ["json", "md", "txt"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_list_formats(test_client):
    response = test_client.get("/api/v1/publish/formats")
    assert response.status_code == 200
    data = response.json()
    assert "json" in data["formats"]
    assert "facebook" in data["formats"]
    assert len(data["formats"]) == 8
