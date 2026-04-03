"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from gandra_tools.core.config import Settings


@pytest.fixture
def test_settings():
    return Settings(
        env="test",
        debug=False,
        secret_key="test-secret-key-for-jwt",
        default_user_email="test@example.com",
        default_user_password="testpass",
        openai_api_key="sk-test-key",
        anthropic_api_key="sk-ant-test-key",
        database_url="sqlite+aiosqlite:///./test_gandra.db",
        output_default_dir="test-output/",
    )


@pytest.fixture
def test_client(test_settings):
    from gandra_tools.core.config import get_settings
    from gandra_tools.main import create_app
    from gandra_tools.routers import auth as auth_router

    # Reset in-memory password store between tests
    auth_router._password_store.clear()

    def override_settings():
        return test_settings

    app = create_app()
    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as client:
        yield client
