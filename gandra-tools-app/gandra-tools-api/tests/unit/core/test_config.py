"""Tests for Settings configuration."""

from gandra_tools.core.config import Settings


def test_default_settings():
    s = Settings(
        secret_key="test",
        openai_api_key="sk-test",
        anthropic_api_key="sk-ant-test",
    )
    assert s.env == "local"
    assert s.debug is True
    assert s.port == 8095
    assert s.default_llm_provider == "openai"
    assert s.default_llm_model == "gpt-4o"
    assert s.output_default_dir == "gandra-output/"


def test_allowed_origins_list():
    s = Settings(
        secret_key="test",
        allowed_origins="http://a.com, http://b.com",
    )
    assert s.allowed_origins_list == ["http://a.com", "http://b.com"]


def test_output_path():
    s = Settings(secret_key="test", output_default_dir="gandra-output/")
    assert str(s.output_path) == "gandra-output"
