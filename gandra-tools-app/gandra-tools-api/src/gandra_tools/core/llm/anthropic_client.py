"""Anthropic (Claude) LLM client."""

from anthropic import AsyncAnthropic

from gandra_tools.core.llm.base import BaseLLMClient, LLMResponse


class AnthropicClient(BaseLLMClient):
    provider = "anthropic"

    def __init__(self, api_key: str, default_model: str = "claude-sonnet-4-6") -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._default_model = default_model

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        model = model or self._default_model
        max_tokens = max_tokens or 4096

        response = await self._client.messages.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            **({"temperature": temperature} if temperature is not None else {}),
        )
        content = response.content[0].text if response.content else ""
        return LLMResponse(
            content=content,
            model=model,
            provider=self.provider,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        raise NotImplementedError("Anthropic does not provide an embedding API.")
