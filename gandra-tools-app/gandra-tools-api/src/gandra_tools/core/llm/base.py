"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict | None = None


class BaseLLMClient(ABC):
    """Abstract LLM client — implemented per provider."""

    provider: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def embed(self, text: str, model: str | None = None) -> list[float]:
        ...
