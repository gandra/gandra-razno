"""Tests for HTML formatter."""

from gandra_tools.core.publisher.formatters.html_formatter import HtmlFormatter


def test_html_has_doctype():
    f = HtmlFormatter()
    result = f.render({"text": "Hello"}, "generic")
    assert "<!DOCTYPE html>" in result


def test_html_contains_content():
    f = HtmlFormatter()
    result = f.render({"summary": "Important finding"}, "generic")
    assert "Important finding" in result


def test_html_has_inline_css():
    f = HtmlFormatter()
    result = f.render({"x": 1}, "generic")
    assert "<style>" in result
