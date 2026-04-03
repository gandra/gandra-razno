"""Ollama (local) LLM client."""

import httpx

from gandra_tools.core.llm.base import BaseLLMClient, LLMResponse


class OllamaClient(BaseLLMClient):
    provider = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.2") -> None:
        self._base_url = base_url.rstrip("/")
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
        payload: dict = {"model": model, "messages": messages, "stream": False}
        options: dict = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if options:
            payload["options"] = options

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=model,
            provider=self.provider,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        )

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        model = model or "nomic-embed-text"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("embeddings", [[]])[0]
