"""Tests for DevTools schemas."""

import pytest
from pydantic import ValidationError

from gandra_tools.tools.devtools.schemas import ApiTestInput, CodeReviewInput, HttpMethod


# ── ApiTestInput ─────────────────────────────────────────────

def test_api_test_valid():
    inp = ApiTestInput(method=HttpMethod.GET, url="https://example.com/api")
    assert inp.method == HttpMethod.GET
    assert inp.timeout_seconds == 30
    assert inp.repeat == 1


def test_api_test_all_methods():
    for m in HttpMethod:
        inp = ApiTestInput(method=m, url="https://x.com")
        assert inp.method == m


def test_api_test_with_body():
    inp = ApiTestInput(method=HttpMethod.POST, url="https://x.com", body={"key": "value"})
    assert inp.body == {"key": "value"}


def test_api_test_with_headers():
    inp = ApiTestInput(
        method=HttpMethod.GET, url="https://x.com", headers={"Authorization": "Bearer xxx"}
    )
    assert inp.headers["Authorization"] == "Bearer xxx"


def test_api_test_timeout_range():
    with pytest.raises(ValidationError):
        ApiTestInput(method=HttpMethod.GET, url="https://x.com", timeout_seconds=0)
    with pytest.raises(ValidationError):
        ApiTestInput(method=HttpMethod.GET, url="https://x.com", timeout_seconds=121)


def test_api_test_repeat_range():
    with pytest.raises(ValidationError):
        ApiTestInput(method=HttpMethod.GET, url="https://x.com", repeat=0)
    with pytest.raises(ValidationError):
        ApiTestInput(method=HttpMethod.GET, url="https://x.com", repeat=101)


# ── CodeReviewInput ──────────────────────────────────────────

def test_code_review_valid():
    inp = CodeReviewInput(path="/some/path")
    assert inp.focus == ["bugs", "security", "performance"]
    assert inp.max_files == 10


def test_code_review_custom_focus():
    inp = CodeReviewInput(path="/p", focus=["security", "style"])
    assert inp.focus == ["security", "style"]


def test_code_review_max_files_range():
    with pytest.raises(ValidationError):
        CodeReviewInput(path="/p", max_files=0)
    with pytest.raises(ValidationError):
        CodeReviewInput(path="/p", max_files=51)
