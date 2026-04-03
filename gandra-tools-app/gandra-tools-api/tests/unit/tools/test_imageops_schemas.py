"""Tests for ImageOps schemas."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from gandra_tools.tools.imageops.schemas import ImageTextExtractInput


def test_valid_local_image():
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake image data")
        path = f.name
    inp = ImageTextExtractInput(image_path=path)
    assert inp.image_path == path


def test_valid_url_image():
    inp = ImageTextExtractInput(image_path="https://example.com/photo.jpg")
    assert inp.image_path.startswith("https://")


def test_nonexistent_file_rejected():
    with pytest.raises(ValidationError, match="does not exist"):
        ImageTextExtractInput(image_path="/nonexistent/photo.jpg")


def test_unsupported_format_rejected():
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as f:
        f.write(b"fake")
        path = f.name
    with pytest.raises(ValidationError, match="Unsupported"):
        ImageTextExtractInput(image_path=path)


def test_confidence_range():
    with pytest.raises(ValidationError):
        ImageTextExtractInput(image_path="https://x.com/i.jpg", min_confidence=-0.1)
    with pytest.raises(ValidationError):
        ImageTextExtractInput(image_path="https://x.com/i.jpg", min_confidence=1.1)


def test_dpi_range():
    with pytest.raises(ValidationError):
        ImageTextExtractInput(image_path="https://x.com/i.jpg", dpi=50)
    with pytest.raises(ValidationError):
        ImageTextExtractInput(image_path="https://x.com/i.jpg", dpi=700)


def test_defaults_applied():
    inp = ImageTextExtractInput(image_path="https://x.com/i.jpg")
    assert inp.mode.value == "ocr"
    assert inp.dpi == 300
    assert inp.min_confidence == 0.5
    assert inp.output_dir == "gandra-output/imageops/"


def test_file_name_auto_generated():
    inp = ImageTextExtractInput(image_path="https://x.com/photo.jpg")
    name = inp.get_resolved_file_name()
    assert "photo" in name
    assert "_text_" in name
    assert "20" in name  # Date


def test_file_name_explicit():
    inp = ImageTextExtractInput(image_path="https://x.com/i.jpg", file_name="my-custom")
    assert inp.get_resolved_file_name() == "my-custom"


def test_full_output_path():
    inp = ImageTextExtractInput(image_path="https://x.com/photo.jpg")
    path = inp.get_full_output_path()
    assert str(path).endswith(".png")
    assert "gandra-output/imageops/" in str(path)
