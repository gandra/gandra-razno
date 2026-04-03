"""Tests for JSON formatter."""

import json

from gandra_tools.core.publisher.formatters.json_formatter import JsonFormatter


def test_format_basic_content():
    f = JsonFormatter()
    result = f.render({"title": "Test", "body": "Hello"}, "generic")
    data = json.loads(result)
    assert data["content_type"] == "generic"
    assert data["data"]["title"] == "Test"


def test_format_with_metadata():
    f = JsonFormatter()
    result = f.render({"x": 1}, "generic", metadata={"author": "Dragan"})
    data = json.loads(result)
    assert data["metadata"]["author"] == "Dragan"


def test_format_unicode():
    f = JsonFormatter()
    result = f.render({"text": "Ćirilica: Здраво свете"}, "generic")
    assert "Здраво свете" in result


def test_format_empty_content():
    f = JsonFormatter()
    result = f.render({}, "generic")
    data = json.loads(result)
    assert data["data"] == {}
