"""Tests for Research service — JSON parsing and helpers."""

import json

from gandra_tools.tools.research.service import ResearchService


def test_parse_json_direct():
    result = ResearchService._parse_json_response('{"key": "value"}')
    assert result == {"key": "value"}


def test_parse_json_from_code_block():
    text = 'Here is the result:\n```json\n{"summary": "hello"}\n```\nDone.'
    result = ResearchService._parse_json_response(text)
    assert result["summary"] == "hello"


def test_parse_json_with_prefix_text():
    text = 'The analysis shows:\n{"score": 0.8, "items": [1, 2, 3]}'
    result = ResearchService._parse_json_response(text)
    assert result["score"] == 0.8


def test_parse_json_array():
    text = '[{"label": "A"}, {"label": "B"}]'
    result = ResearchService._parse_json_response(text)
    assert isinstance(result, list)
    assert len(result) == 2


def test_parse_json_invalid_returns_empty():
    result = ResearchService._parse_json_response("This is not JSON at all")
    assert result == {}


def test_parse_json_code_block_no_lang():
    text = '```\n{"data": true}\n```'
    result = ResearchService._parse_json_response(text)
    assert result["data"] is True
