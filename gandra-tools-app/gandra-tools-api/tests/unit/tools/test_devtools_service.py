"""Tests for DevTools service — file collection."""

import tempfile
from pathlib import Path

from gandra_tools.tools.devtools.schemas import CodeReviewInput
from gandra_tools.tools.devtools.service import CodeReviewService


def test_collect_single_file():
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write("print('hello')")
        path = f.name

    svc = CodeReviewService()
    files = svc._collect_files(Path(path), CodeReviewInput(path=path))
    assert len(files) == 1


def test_collect_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.py").write_text("import os")
        (Path(tmpdir) / "utils.py").write_text("def util(): pass")
        (Path(tmpdir) / "readme.txt").write_text("not code")  # Not in suffix list

        svc = CodeReviewService()
        files = svc._collect_files(Path(tmpdir), CodeReviewInput(path=tmpdir))
        assert len(files) == 2


def test_collect_respects_max_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(20):
            (Path(tmpdir) / f"file{i}.py").write_text(f"# file {i}")

        svc = CodeReviewService()
        files = svc._collect_files(Path(tmpdir), CodeReviewInput(path=tmpdir, max_files=5))
        assert len(files) == 5


def test_collect_ignores_patterns():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.py").write_text("main code")
        (Path(tmpdir) / "app.test.py").write_text("test code")

        svc = CodeReviewService()
        files = svc._collect_files(
            Path(tmpdir), CodeReviewInput(path=tmpdir, ignore_patterns=["*.test.*"])
        )
        names = [f.name for f in files]
        assert "app.py" in names
        assert "app.test.py" not in names


def test_build_context():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text("def hello():\n    print('hi')")

        svc = CodeReviewService()
        files = [Path(tmpdir) / "main.py"]
        context = svc._build_context(files, CodeReviewInput(path=tmpdir))
        assert "def hello():" in context
        assert "main.py" in context
