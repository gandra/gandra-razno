"""Tests for ImageOps service — mocked OCR and Pillow."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gandra_tools.tools.imageops.schemas import TextRegion
from gandra_tools.tools.imageops.service import _parse_color


# ── Helper tests ─────────────────────────────────────────────

def test_parse_color_hex():
    assert _parse_color("#ff0000") == (255, 0, 0)
    assert _parse_color("#000000") == (0, 0, 0)


def test_parse_color_named():
    assert _parse_color("black") == (0, 0, 0)
    assert _parse_color("white") == (255, 255, 255)


def test_parse_color_unknown_defaults_black():
    assert _parse_color("magenta") == (0, 0, 0)


# ── Service with mocked OCR ─────────────────────────────────

MOCK_OCR_RESULTS = [
    ([[10, 10], [100, 10], [100, 40], [10, 40]], "Hello World", 0.95),
    ([[10, 60], [150, 60], [150, 90], [10, 90]], "Some text here", 0.88),
    ([[10, 110], [80, 110], [80, 130], [10, 130]], "Low conf", 0.3),
]


@pytest.fixture
def mock_image():
    """Create a real temporary image file using Pillow."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f, "PNG")
        return f.name


def test_service_extract_with_mocked_ocr(mock_image):
    """Test full extract pipeline with mocked EasyOCR."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    from gandra_tools.tools.imageops.schemas import ImageTextExtractInput
    from gandra_tools.tools.imageops.service import ImageTextExtractService

    with tempfile.TemporaryDirectory() as tmpdir:
        input_data = ImageTextExtractInput(
            image_path=mock_image,
            output_dir=tmpdir,
            min_confidence=0.5,
        )

        mock_reader = MagicMock()
        mock_reader.readtext.return_value = MOCK_OCR_RESULTS

        with patch("gandra_tools.tools.imageops.service.ImageTextExtractService._ocr_detect") as mock_detect:
            mock_detect.return_value = [
                TextRegion(text="Hello World", confidence=0.95, bbox=(10, 10, 100, 40), font_size_estimate=30),
                TextRegion(text="Some text here", confidence=0.88, bbox=(10, 60, 150, 90), font_size_estimate=30),
                TextRegion(text="Low conf", confidence=0.3, bbox=(10, 110, 80, 130), font_size_estimate=20),
            ]

            service = ImageTextExtractService()
            result = service.extract(input_data)

        assert result.regions_detected == 3
        assert result.regions_included == 2  # Low conf filtered out
        assert "Hello World" in result.extracted_text
        assert "Some text here" in result.extracted_text
        assert "Low conf" not in result.extracted_text
        assert Path(result.output_path).exists()
        assert result.file_size_bytes > 0

        # Verify output is RGBA PNG
        output_img = Image.open(result.output_path)
        assert output_img.mode == "RGBA"


def test_confidence_filter():
    """Verify confidence filter works correctly."""
    regions = [
        TextRegion(text="high", confidence=0.9, bbox=(0, 0, 10, 10)),
        TextRegion(text="medium", confidence=0.6, bbox=(0, 0, 10, 10)),
        TextRegion(text="low", confidence=0.3, bbox=(0, 0, 10, 10)),
    ]
    filtered = [r for r in regions if r.confidence >= 0.5]
    assert len(filtered) == 2
    assert filtered[0].text == "high"
    assert filtered[1].text == "medium"
