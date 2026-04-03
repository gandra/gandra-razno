"""LLM Factory — creates provider clients with BYOK support."""

from gandra_tools.core.config import Settings, get_settings
from gandra_tools.core.llm.anthropic_client import AnthropicClient
from gandra_tools.core.llm.base import BaseLLMClient
from gandra_tools.core.llm.ollama_client import OllamaClient
from gandra_tools.core.llm.openai_client import OpenAIClient

PROVIDERS = {"openai", "anthropic", "ollama"}


class LLMFactory:
    """Creates LLM clients. Supports BYOK key override per request."""

    @staticmethod
    def get_client(
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        settings: Settings | None = None,
    ) -> BaseLLMClient:
        if settings is None:
            settings = get_settings()

        provider = provider or settings.default_llm_provider
        model = model or settings.default_llm_model

        if provider == "openai":
            key = api_key or settings.openai_api_key
            if not key:
                raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY or pass api_key.")
            return OpenAIClient(api_key=key, default_model=model)

        if provider == "anthropic":
            key = api_key or settings.anthropic_api_key
            if not key:
                raise ValueError(
                    "Anthropic API key not configured. Set ANTHROPIC_API_KEY or pass api_key."
                )
            return AnthropicClient(api_key=key, default_model=model)

        if provider == "ollama":
            base_url = settings.ollama_base_url
            return OllamaClient(base_url=base_url, default_model=model)

        raise ValueError(f"Unknown LLM provider: '{provider}'. Supported: {PROVIDERS}")
