"""YouTube tool schemas."""

import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from gandra_tools.models.schemas import OutputFormat, ToolInputBase

DEFAULT_OUTPUT_DIR = "gandra-output/youtube/"


def slugify_title(title: str, max_length: int = 80) -> str:
    """Slugify a video title for use as filename."""
    # Transliterate common Cyrillic
    _cyr_lat = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ђ": "dj", "е": "e",
        "ж": "z", "з": "z", "и": "i", "ј": "j", "к": "k", "л": "l", "љ": "lj",
        "м": "m", "н": "n", "њ": "nj", "о": "o", "п": "p", "р": "r", "с": "s",
        "т": "t", "ћ": "c", "у": "u", "ф": "f", "х": "h", "ц": "c", "ч": "c",
        "џ": "dz", "ш": "s",
    }
    text = title.lower()
    text = "".join(_cyr_lat.get(c, c) for c in text)
    # Remove emoji and special chars
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text.strip())
    text = re.sub(r"-+", "-", text).strip("-")
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text or "transcript"


class TranscriptInput(ToolInputBase):
    """Input for YouTube transcript extraction."""

    url: str
    output_dir: str = Field(default=DEFAULT_OUTPUT_DIR)
    file_name: str | None = None
    interval_minutes: int = Field(default=2, ge=1, le=30)
    language: str = Field(default="auto")
    include_timestamps: bool = True
    merge_short_segments: bool = True

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("URL must be a YouTube link")
        return v

    def get_resolved_file_name(self, video_title: str) -> str:
        if self.file_name:
            return self.file_name
        slug = slugify_title(video_title)
        return f"{slug}_{date.today():%Y%m%d}"

    def get_full_output_path(self, video_title: str) -> Path:
        name = self.get_resolved_file_name(video_title)
        ext = self.output_format.value
        return Path(self.output_dir) / f"{name}.{ext}"


class TranscriptSegment(BaseModel):
    """A single transcript segment."""

    start_time: float
    end_time: float
    start_formatted: str
    end_formatted: str
    text: str


class TranscriptOutput(BaseModel):
    """Output from YouTube transcript extraction."""

    video_title: str
    video_url: str
    video_duration_seconds: int
    duration_formatted: str
    language: str
    segment_count: int
    word_count: int
    segments: list[TranscriptSegment]
    full_text: str
    file_path: str | None = None
    metadata: dict = Field(default_factory=dict)
