"""Tests for Markdown formatter."""

from gandra_tools.core.publisher.formatters.markdown_formatter import MarkdownFormatter


def test_generic_template_renders():
    f = MarkdownFormatter()
    result = f.render({"summary": "Test summary", "items": ["a", "b"]}, "generic")
    assert "# Generic" in result or "# " in result
    assert "Test summary" in result


def test_unknown_content_type_falls_back_to_generic():
    f = MarkdownFormatter()
    result = f.render({"data": "hello"}, "nonexistent_type_xyz")
    assert "hello" in result


def test_metadata_rendered():
    f = MarkdownFormatter()
    result = f.render({"x": 1}, "generic", metadata={"title": "My Report", "date": "2026-04-03"})
    assert "My Report" in result
