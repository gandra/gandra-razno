"""Abstract base formatter."""

from abc import ABC, abstractmethod

from gandra_tools.models.schemas import OutputFormat


class BaseFormatter(ABC):
    """Base class for all output formatters."""

    format: OutputFormat
    mime_type: str
    file_extension: str

    @abstractmethod
    def render(self, content: dict, content_type: str, metadata: dict | None = None, **options) -> str:
        """Render content dict into formatted string."""
        ...
