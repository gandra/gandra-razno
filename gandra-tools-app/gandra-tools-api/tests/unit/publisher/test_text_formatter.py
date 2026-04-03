"""Tests for Text formatter."""

from gandra_tools.core.publisher.formatters.text_formatter import TextFormatter


def test_format_basic():
    f = TextFormatter()
    result = f.render({"summary": "Hello world"}, "generic")
    assert "summary: Hello world" in result


def test_format_list_values():
    f = TextFormatter()
    result = f.render({"items": ["a", "b", "c"]}, "generic")
    assert "- a" in result
    assert "- c" in result


def test_format_with_title_metadata():
    f = TextFormatter()
    result = f.render({"x": 1}, "generic", metadata={"title": "Report"})
    assert "REPORT" in result
    assert "=====" in result


def test_format_dict_values():
    f = TextFormatter()
    result = f.render({"scores": {"a": 0.8, "b": 0.5}}, "generic")
    assert "a: 0.8" in result
