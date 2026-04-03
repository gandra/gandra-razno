"""Tests for YouTube service — mocked YT API."""

from gandra_tools.tools.youtube.service import _extract_video_id, _format_time, _merge_segments


# ── Helpers ──────────────────────────────────────────────────

def test_format_time_minutes():
    assert _format_time(0) == "00:00"
    assert _format_time(65) == "01:05"
    assert _format_time(3661) == "01:01:01"


def test_extract_video_id_standard():
    assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_short():
    assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_with_params():
    assert _extract_video_id("https://youtube.com/watch?v=abc123def45&t=30") == "abc123def45"


# ── Segment merging ──────────────────────────────────────────

MOCK_RAW_SEGMENTS = [
    {"start": 0.0, "duration": 5.0, "text": "Hello everyone."},
    {"start": 5.0, "duration": 4.0, "text": "Welcome to this video."},
    {"start": 60.0, "duration": 5.0, "text": "Let's start with the basics."},
    {"start": 65.0, "duration": 5.0, "text": "First, install Python."},
    {"start": 125.0, "duration": 5.0, "text": "Now let's write some code."},
    {"start": 130.0, "duration": 5.0, "text": "Open your editor."},
]


def test_merge_by_1_minute_interval():
    segments = _merge_segments(MOCK_RAW_SEGMENTS, interval_minutes=1, merge_short=True)
    assert len(segments) == 3
    assert "Hello everyone" in segments[0].text
    assert "Welcome" in segments[0].text
    assert segments[0].start_formatted == "00:00"


def test_merge_by_2_minute_interval():
    segments = _merge_segments(MOCK_RAW_SEGMENTS, interval_minutes=2, merge_short=True)
    assert len(segments) == 2


def test_merge_empty():
    segments = _merge_segments([], interval_minutes=2, merge_short=True)
    assert segments == []


def test_merge_single_segment():
    raw = [{"start": 0.0, "duration": 10.0, "text": "Only one."}]
    segments = _merge_segments(raw, interval_minutes=2, merge_short=True)
    assert len(segments) == 1
    assert segments[0].text == "Only one."


def test_segment_timestamps_formatted():
    segments = _merge_segments(MOCK_RAW_SEGMENTS, interval_minutes=1, merge_short=True)
    assert segments[1].start_formatted == "01:00"
