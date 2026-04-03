"""Tests for main CLI entry point and autodiscovery."""

from typer.testing import CliRunner

from gandra_tools.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "gandra-tools" in result.output.lower() or "Swiss-army" in result.output


def test_youtube_subcommand_discovered():
    result = runner.invoke(app, ["youtube", "--help"])
    assert result.exit_code == 0
    assert "transcript" in result.output.lower()


def test_config_show():
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "llm.provider" in result.output
    assert "default" in result.output or "global" in result.output


def test_config_show_category():
    result = runner.invoke(app, ["config", "show", "--category", "llm"])
    assert result.exit_code == 0
    assert "llm.provider" in result.output
    # Should not show non-llm keys
    assert "system.debug" not in result.output


def test_env_current_no_active():
    result = runner.invoke(app, ["env", "current"])
    assert result.exit_code == 0
    assert "No active" in result.output


def test_env_set_and_current():
    # Set env
    result = runner.invoke(app, ["env", "set", "office-dt"])
    assert result.exit_code == 0
    assert "office-dt" in result.output


def test_publish_formats():
    result = runner.invoke(app, ["publish", "formats"])
    assert result.exit_code == 0
    assert "json" in result.output
    assert "facebook" in result.output
    assert "x" in result.output


def test_publish_file_not_found():
    result = runner.invoke(app, ["publish", "file", "/nonexistent/file.json"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()
