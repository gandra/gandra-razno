"""Tests for auth module."""

from gandra_tools.core.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from gandra_tools.core.config import Settings


def _test_settings():
    return Settings(secret_key="test-secret-key")


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed)
    assert not verify_password("wrongpass", hashed)


def test_create_and_decode_token():
    settings = _test_settings()
    token = create_access_token("user@example.com", settings)
    payload = decode_token(token, settings)
    assert payload is not None
    assert payload.sub == "user@example.com"


def test_decode_invalid_token():
    settings = _test_settings()
    payload = decode_token("invalid.token.here", settings)
    assert payload is None


def test_decode_wrong_secret():
    settings = _test_settings()
    token = create_access_token("user@example.com", settings)
    other_settings = Settings(secret_key="different-key")
    payload = decode_token(token, other_settings)
    assert payload is None
