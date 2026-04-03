"""File operations schemas."""

from enum import Enum

from pydantic import BaseModel, Field

from gandra_tools.models.schemas import ToolInputBase


class RenameStrategy(str, Enum):
    SLUGIFY = "slugify"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    SNAKE_CASE = "snake_case"
    KEBAB_CASE = "kebab-case"
    CAMEL_CASE = "camelCase"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    REGEX = "regex"
    DATE_PREFIX = "date_prefix"


class FileSearchInput(ToolInputBase):
    """Input for file search."""

    path: str = Field(..., description="Directory to search in")
    pattern: str = Field(default="*", description="Glob pattern for file names")
    content: str | None = Field(default=None, description="Search inside file content (regex)")
    recursive: bool = True
    max_results: int = Field(default=100, ge=1, le=1000)
    include_hidden: bool = False


class FileSearchResult(BaseModel):
    """A single search result."""

    path: str
    name: str
    size_bytes: int
    modified: str
    content_match: str | None = None  # Matching line if content search


class FileSearchOutput(BaseModel):
    """Output from file search."""

    query_path: str
    pattern: str
    content_query: str | None
    total_found: int
    results: list[FileSearchResult]


class FileRenameInput(ToolInputBase):
    """Input for batch rename."""

    path: str = Field(..., description="Directory with files to rename")
    strategy: RenameStrategy
    prefix: str | None = None
    suffix: str | None = None
    pattern: str | None = Field(default=None, description="Regex pattern to match")
    replacement: str | None = Field(default=None, description="Regex replacement string")
    file_pattern: str = Field(default="*", description="Glob pattern to select files")
    dry_run: bool = Field(default=True, description="Preview only, no actual rename")
    recursive: bool = False


class RenamePreview(BaseModel):
    """Preview of a single rename operation."""

    original: str
    renamed: str
    status: str = "pending"  # pending, renamed, skipped, error


class FileRenameOutput(BaseModel):
    """Output from batch rename."""

    strategy: RenameStrategy
    dry_run: bool
    total_files: int
    renamed_count: int
    skipped_count: int
    previews: list[RenamePreview]
