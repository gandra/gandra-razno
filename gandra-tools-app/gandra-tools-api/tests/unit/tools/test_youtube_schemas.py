"""Tests for YouTube schemas."""

import pytest
from pydantic import ValidationError

from gandra_tools.tools.youtube.schemas import TranscriptInput, slugify_title


# ── slugify_title ────────────────────────────────────────────

def test_slugify_basic():
    assert slugify_title("How to Build a REST API") == "how-to-build-a-rest-api"


def test_slugify_cyrillic():
    result = slugify_title("Здраво свете")
    assert "z" in result  # Transliterated
    assert " " not in result


def test_slugify_emoji_removed():
    result = slugify_title("React vs Vue 2026 🔥")
    assert "🔥" not in result
    assert "react-vs-vue-2026" == result


def test_slugify_max_length():
    long_title = "a " * 100
    result = slugify_title(long_title, max_length=80)
    assert len(result) <= 80


def test_slugify_empty():
    assert slugify_title("") == "transcript"


# ── TranscriptInput validation ───────────────────────────────

def test_valid_youtube_url():
    inp = TranscriptInput(url="https://youtube.com/watch?v=abc123")
    assert inp.url == "https://youtube.com/watch?v=abc123"


def test_valid_short_url():
    inp = TranscriptInput(url="https://youtu.be/abc123")
    assert "youtu.be" in inp.url


def test_invalid_url_rejected():
    with pytest.raises(ValidationError, match="YouTube link"):
        TranscriptInput(url="https://example.com/video")


def test_defaults_applied():
    inp = TranscriptInput(url="https://youtube.com/watch?v=test")
    assert inp.interval_minutes == 2
    assert inp.language == "auto"
    assert inp.output_dir == "gandra-output/youtube/"
    assert inp.include_timestamps is True


def test_interval_range():
    with pytest.raises(ValidationError):
        TranscriptInput(url="https://youtube.com/watch?v=x", interval_minutes=0)
    with pytest.raises(ValidationError):
        TranscriptInput(url="https://youtube.com/watch?v=x", interval_minutes=31)


def test_file_name_auto_generated():
    inp = TranscriptInput(url="https://youtube.com/watch?v=x")
    name = inp.get_resolved_file_name("How to Build an API")
    assert "how-to-build-an-api" in name
    assert "_20" in name  # Date suffix


def test_file_name_explicit():
    inp = TranscriptInput(url="https://youtube.com/watch?v=x", file_name="my-custom-name")
    assert inp.get_resolved_file_name("Anything") == "my-custom-name"


def test_full_output_path():
    inp = TranscriptInput(url="https://youtube.com/watch?v=x")
    path = inp.get_full_output_path("Test Video")
    assert str(path).startswith("gandra-output/youtube/")
    assert str(path).endswith(".md")
