"""DevTools schemas."""

from enum import Enum

from pydantic import BaseModel, Field

from gandra_tools.models.schemas import ToolInputBase


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ApiTestInput(ToolInputBase):
    """Input for API testing."""

    method: HttpMethod
    url: str
    headers: dict[str, str] | None = None
    body: dict | str | None = None
    expected_status: int | None = None
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    repeat: int = Field(default=1, ge=1, le=100)


class ApiTestResult(BaseModel):
    """Result of a single API call."""

    status_code: int
    response_time_ms: int
    headers: dict[str, str]
    body_preview: str
    body_size_bytes: int
    success: bool


class ApiTestOutput(BaseModel):
    """Output from API testing."""

    method: str
    url: str
    repeat_count: int
    results: list[ApiTestResult]
    avg_response_time_ms: float
    all_passed: bool
    expected_status: int | None = None


class CodeReviewInput(ToolInputBase):
    """Input for AI code review."""

    path: str
    language: str | None = None
    focus: list[str] = Field(default=["bugs", "security", "performance"])
    max_files: int = Field(default=10, ge=1, le=50)
    ignore_patterns: list[str] = Field(default=["*.test.*", "__pycache__", ".venv"])


class CodeReviewFinding(BaseModel):
    """A single finding from code review."""

    file: str
    line: int | None = None
    severity: str  # info, warning, error, critical
    category: str  # bugs, security, performance, style
    message: str
    suggestion: str | None = None


class CodeReviewOutput(BaseModel):
    """Output from AI code review."""

    files_reviewed: int
    total_findings: int
    findings: list[CodeReviewFinding]
    summary: str
    file_path: str | None = None
