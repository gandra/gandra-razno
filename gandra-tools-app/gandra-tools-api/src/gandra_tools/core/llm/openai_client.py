"""OpenAI LLM client."""

from openai import AsyncOpenAI

from gandra_tools.core.llm.base import BaseLLMClient, LLMResponse


class OpenAIClient(BaseLLMClient):
    provider = "openai"

    def __init__(self, api_key: str, default_model: str = "gpt-4o") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
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
        params: dict = {"model": model, "messages": messages}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        response = await self._client.chat.completions.create(**params)
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=model,
            provider=self.provider,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        model = model or "text-embedding-3-small"
        response = await self._client.embeddings.create(model=model, input=text)
        return response.data[0].embedding
