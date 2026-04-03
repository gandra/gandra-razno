"""Tests for LLM Factory."""

import pytest

from gandra_tools.core.config import Settings
from gandra_tools.core.llm.factory import LLMFactory
from gandra_tools.core.llm.anthropic_client import AnthropicClient
from gandra_tools.core.llm.ollama_client import OllamaClient
from gandra_tools.core.llm.openai_client import OpenAIClient


def _settings(**kwargs):
    defaults = {
        "secret_key": "test",
        "openai_api_key": "sk-test",
        "anthropic_api_key": "sk-ant-test",
        "ollama_base_url": "http://localhost:11434",
    }
    defaults.update(kwargs)
    return Settings(**defaults)


def test_create_openai_client():
    client = LLMFactory.get_client("openai", settings=_settings())
    assert isinstance(client, OpenAIClient)
    assert client.provider == "openai"


def test_create_anthropic_client():
    client = LLMFactory.get_client("anthropic", settings=_settings())
    assert isinstance(client, AnthropicClient)
    assert client.provider == "anthropic"


def test_create_ollama_client():
    client = LLMFactory.get_client("ollama", settings=_settings())
    assert isinstance(client, OllamaClient)
    assert client.provider == "ollama"


def test_default_provider_from_settings():
    s = _settings(default_llm_provider="anthropic")
    client = LLMFactory.get_client(settings=s)
    assert isinstance(client, AnthropicClient)


def test_byok_key_override():
    client = LLMFactory.get_client("openai", api_key="sk-custom", settings=_settings())
    assert isinstance(client, OpenAIClient)


def test_unknown_provider_error():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        LLMFactory.get_client("google", settings=_settings())


def test_missing_api_key_error():
    s = _settings(openai_api_key="")
    with pytest.raises(ValueError, match="API key not configured"):
        LLMFactory.get_client("openai", settings=s)
