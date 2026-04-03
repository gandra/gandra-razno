"""Image Text Extractor schemas."""

import re
from datetime import date
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from gandra_tools.models.schemas import ToolInputBase

DEFAULT_OUTPUT_DIR = "gandra-output/imageops/"

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}


class ImageExtractMode(str, Enum):
    OCR = "ocr"
    MASK = "mask"


class ImageTextExtractInput(ToolInputBase):
    """Input for image text extraction."""

    image_path: str
    output_dir: str = Field(default=DEFAULT_OUTPUT_DIR)
    file_name: str | None = None
    mode: ImageExtractMode = ImageExtractMode.OCR
    language: str = Field(default="auto")
    font_color: str = Field(default="auto")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    preserve_layout: bool = True
    extract_text: bool = True
    dpi: int = Field(default=300, ge=72, le=600)

    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        if v.startswith(("http://", "https://")):
            return v
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {v}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported image format: {path.suffix}")
        return v

    def get_resolved_file_name(self) -> str:
        if self.file_name:
            return self.file_name
        if self.image_path.startswith(("http://", "https://")):
            # Extract filename from URL
            from urllib.parse import urlparse

            parsed = urlparse(self.image_path)
            stem = Path(parsed.path).stem or "image"
        else:
            stem = Path(self.image_path).stem
        slug = re.sub(r"[^\w\s-]", "", stem.lower())
        slug = re.sub(r"[\s_]+", "-", slug).strip("-") or "image"
        return f"{slug}_text_{date.today():%Y%m%d}"

    def get_full_output_path(self) -> Path:
        name = self.get_resolved_file_name()
        return Path(self.output_dir) / f"{name}.png"


class TextRegion(BaseModel):
    """A detected text region."""

    text: str
    confidence: float
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    font_size_estimate: int | None = None
    color_hex: str | None = None


class ImageTextExtractOutput(BaseModel):
    """Output from text extraction."""

    output_path: str
    input_path: str
    mode: ImageExtractMode
    image_dimensions: tuple[int, int]
    regions_detected: int
    regions_included: int
    extracted_text: str | None = None
    regions: list[TextRegion]
    processing_time_ms: int
    file_size_bytes: int
