"""Tests for PublisherService."""

import json
import tempfile
from pathlib import Path

import pytest

from gandra_tools.core.publisher.service import PublisherService
from gandra_tools.core.publisher.schemas import PublishRequest
from gandra_tools.models.schemas import OutputFormat


@pytest.fixture
def publisher():
    return PublisherService()


SAMPLE = {"title": "Test Report", "summary": "A test summary."}


def test_publish_json(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.JSON))
    assert resp.format == OutputFormat.JSON
    assert resp.content_type_mime == "application/json"
    data = json.loads(resp.content)
    assert data["data"]["title"] == "Test Report"


def test_publish_markdown(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.MARKDOWN))
    assert resp.format == OutputFormat.MARKDOWN
    assert "Test Report" in resp.content or "test report" in resp.content.lower()


def test_publish_text(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.TEXT))
    assert resp.content_type_mime == "text/plain"
    assert "summary: A test summary." in resp.content


def test_publish_html(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.HTML))
    assert "<!DOCTYPE html>" in resp.content


def test_publish_to_file(publisher):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "test.json")
        resp = publisher.publish(
            PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.JSON, output_path=path)
        )
        assert resp.file_path == path
        assert Path(path).exists()
        saved = json.loads(Path(path).read_text())
        assert saved["data"]["title"] == "Test Report"


def test_publish_return_content_no_file(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.JSON))
    assert resp.file_path is None
    assert resp.size_bytes > 0


def test_publish_multi(publisher):
    results = publisher.publish_multi(SAMPLE, "generic", [OutputFormat.JSON, OutputFormat.MARKDOWN, OutputFormat.TEXT])
    assert len(results) == 3
    formats = {r.format for r in results}
    assert formats == {OutputFormat.JSON, OutputFormat.MARKDOWN, OutputFormat.TEXT}


def test_publish_facebook(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.FACEBOOK))
    assert resp.content_type_mime == "text/plain"
    assert "Test Report" in resp.content


def test_publish_linkedin(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.LINKEDIN))
    assert "Test Report" in resp.content


def test_publish_x(publisher):
    resp = publisher.publish(PublishRequest(content=SAMPLE, content_type="generic", format=OutputFormat.X))
    assert "🧵" in resp.content


def test_get_supported_formats(publisher):
    formats = publisher.get_supported_formats()
    assert "json" in formats
    assert "facebook" in formats
    assert "x" in formats
    assert len(formats) == 8
