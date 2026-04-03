"""Tests for error classes."""

from gandra_tools.core.errors import ProviderError, ToolError, ToolNotFoundError


def test_tool_error():
    err = ToolError("something broke", status_code=400)
    assert err.message == "something broke"
    assert err.status_code == 400
    assert str(err) == "something broke"


def test_tool_not_found():
    err = ToolNotFoundError("magic-tool")
    assert "magic-tool" in err.message
    assert err.status_code == 404


def test_provider_error():
    err = ProviderError("openai", "rate limit exceeded")
    assert "openai" in err.message
    assert "rate limit" in err.message
    assert err.status_code == 502
