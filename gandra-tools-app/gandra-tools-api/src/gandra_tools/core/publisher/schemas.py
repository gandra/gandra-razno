"""Publisher schemas — request/response models."""

from pydantic import BaseModel

from gandra_tools.models.schemas import OutputFormat


class PublishRequest(BaseModel):
    """Request to publish content in a specific format."""

    content: dict
    content_type: str  # "research_analysis", "youtube_transcript", "generic"
    format: OutputFormat
    template: str | None = None  # Custom template override
    output_path: str | None = None  # Where to save (None = return in response)
    metadata: dict | None = None
    options: dict | None = None  # Format-specific options


class PublishResponse(BaseModel):
    """Result of a publish operation."""

    format: OutputFormat
    content: str
    file_path: str | None = None
    size_bytes: int
    content_type_mime: str


class MultiPublishRequest(BaseModel):
    """Publish same content in multiple formats."""

    content: dict
    content_type: str
    formats: list[OutputFormat]
    metadata: dict | None = None
