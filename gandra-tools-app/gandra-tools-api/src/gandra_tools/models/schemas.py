"""Shared Pydantic schemas."""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class OutputFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "md"
    TEXT = "txt"
    HTML = "html"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    X = "x"


class ToolInputBase(BaseModel):
    """Base model for all tool inputs."""

    model_config = ConfigDict(extra="forbid")

    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_options: dict | None = None
    output_format: OutputFormat = OutputFormat.MARKDOWN
    output_path: str | None = None


class ToolInfo(BaseModel):
    name: str
    display_name: str
    category: str
    description: str
    version: str
    tools: list[dict]
