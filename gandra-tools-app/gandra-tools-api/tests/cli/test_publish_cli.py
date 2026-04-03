"""Tests for publish CLI commands."""

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from gandra_tools.cli import app

runner = CliRunner()


def test_publish_json_to_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test.json"
        input_path.write_text(json.dumps({"title": "Test", "summary": "Hello"}))

        output_path = Path(tmpdir) / "test.md"
        result = runner.invoke(
            app, ["publish", "file", str(input_path), "--format", "md", "--output", str(output_path)]
        )
        assert result.exit_code == 0
        assert "Published" in result.output
        assert output_path.exists()
        content = output_path.read_text()
        assert "Hello" in content


def test_publish_json_to_txt():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "data.json"
        input_path.write_text(json.dumps({"key": "value"}))

        result = runner.invoke(app, ["publish", "file", str(input_path), "--format", "txt"])
        assert result.exit_code == 0
        assert "Published" in result.output


def test_publish_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "bad.json"
        input_path.write_text("not valid json {{{")

        result = runner.invoke(app, ["publish", "file", str(input_path)])
        assert result.exit_code == 1
        assert "Invalid JSON" in result.output


def test_publish_unknown_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test.json"
        input_path.write_text(json.dumps({"x": 1}))

        result = runner.invoke(app, ["publish", "file", str(input_path), "--format", "pdf"])
        assert result.exit_code == 1
        assert "Unknown format" in result.output
