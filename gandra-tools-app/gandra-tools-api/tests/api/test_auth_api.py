"""Tests for auth API endpoints."""


def test_login_valid_credentials(test_client, test_settings):
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_settings.default_user_email,
            "password": test_settings.default_user_password,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(test_client, test_settings):
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": test_settings.default_user_email, "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_login_unknown_user(test_client):
    response = test_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "pass"},
    )
    assert response.status_code == 401


def _get_token(test_client, test_settings) -> str:
    resp = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_settings.default_user_email,
            "password": test_settings.default_user_password,
        },
    )
    return resp.json()["access_token"]


def test_change_password_success(test_client, test_settings):
    token = _get_token(test_client, test_settings)
    response = test_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": test_settings.default_user_password,
            "new_password": "newsecret123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_change_password_wrong_current(test_client, test_settings):
    token = _get_token(test_client, test_settings)
    response = test_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongpass", "new_password": "newsecret"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_change_password_no_auth(test_client):
    response = test_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "x", "new_password": "y"},
    )
    assert response.status_code == 401
