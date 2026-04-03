"""Tests for FileOps service — rename strategies and search."""

import tempfile
from pathlib import Path

from gandra_tools.tools.fileops.schemas import FileRenameInput, FileSearchInput, RenameStrategy
from gandra_tools.tools.fileops.service import FileOpsService, _apply_strategy

# ── Rename strategy tests ────────────────────────────────────


def test_slugify():
    assert _apply_strategy("My File (1).txt", RenameStrategy.SLUGIFY) == "my-file-1.txt"


def test_slugify_spaces_and_special():
    assert _apply_strategy("Hello   World!!.pdf", RenameStrategy.SLUGIFY) == "hello-world.pdf"


def test_uppercase():
    assert _apply_strategy("report.txt", RenameStrategy.UPPERCASE) == "REPORT.txt"


def test_lowercase():
    assert _apply_strategy("MyFile.TXT", RenameStrategy.LOWERCASE) == "myfile.TXT"


def test_snake_case():
    assert _apply_strategy("myFileName.py", RenameStrategy.SNAKE_CASE) == "my_file_name.py"


def test_snake_case_from_spaces():
    assert _apply_strategy("My File Name.txt", RenameStrategy.SNAKE_CASE) == "my_file_name.txt"


def test_kebab_case():
    assert _apply_strategy("myFileName.js", RenameStrategy.KEBAB_CASE) == "my-file-name.js"


def test_camel_case():
    assert _apply_strategy("my_file_name.py", RenameStrategy.CAMEL_CASE) == "myFileName.py"


def test_prefix():
    assert _apply_strategy("file.txt", RenameStrategy.PREFIX, prefix="2026_") == "2026_file.txt"


def test_suffix():
    assert _apply_strategy("file.txt", RenameStrategy.SUFFIX, suffix="_backup") == "file_backup.txt"


def test_date_prefix():
    result = _apply_strategy("file.txt", RenameStrategy.DATE_PREFIX)
    assert result.endswith("_file.txt")
    assert "20" in result  # Year prefix


def test_regex():
    result = _apply_strategy("IMG_001.jpg", RenameStrategy.REGEX, pattern=r"IMG_(\d+)", replacement=r"photo_\1")
    assert result == "photo_001.jpg"


# ── Search service tests ─────────────────────────────────────


def test_search_by_pattern():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "test.py").write_text("print('hello')")
        (Path(tmpdir) / "test.txt").write_text("some text")
        (Path(tmpdir) / "other.js").write_text("console.log()")

        svc = FileOpsService()
        result = svc.search(FileSearchInput(path=tmpdir, pattern="*.py"))
        assert result.total_found == 1
        assert result.results[0].name == "test.py"


def test_search_by_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "a.txt").write_text("def main():\n    pass")
        (Path(tmpdir) / "b.txt").write_text("no match here")

        svc = FileOpsService()
        result = svc.search(FileSearchInput(path=tmpdir, pattern="*.txt", content="def main"))
        assert result.total_found == 1
        assert "def main" in result.results[0].content_match


def test_search_recursive():
    with tempfile.TemporaryDirectory() as tmpdir:
        sub = Path(tmpdir) / "sub"
        sub.mkdir()
        (sub / "deep.py").write_text("deep file")
        (Path(tmpdir) / "top.py").write_text("top file")

        svc = FileOpsService()
        result = svc.search(FileSearchInput(path=tmpdir, pattern="*.py", recursive=True))
        assert result.total_found == 2


def test_search_nonexistent_dir():
    import pytest

    svc = FileOpsService()
    with pytest.raises(ValueError, match="does not exist"):
        svc.search(FileSearchInput(path="/nonexistent/dir"))


# ── Rename service tests ─────────────────────────────────────


def test_rename_dry_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "My File.txt").write_text("content")
        (Path(tmpdir) / "Another File.txt").write_text("content")

        svc = FileOpsService()
        result = svc.rename(
            FileRenameInput(path=tmpdir, strategy=RenameStrategy.SLUGIFY, dry_run=True)
        )
        assert result.dry_run is True
        assert result.renamed_count == 2
        # Files should NOT be renamed
        assert (Path(tmpdir) / "My File.txt").exists()


def test_rename_execute():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "My File.txt").write_text("content")

        svc = FileOpsService()
        result = svc.rename(
            FileRenameInput(path=tmpdir, strategy=RenameStrategy.SLUGIFY, dry_run=False)
        )
        assert result.dry_run is False
        assert result.renamed_count == 1
        assert (Path(tmpdir) / "my-file.txt").exists()
        assert not (Path(tmpdir) / "My File.txt").exists()


def test_rename_skips_unchanged():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "already-slugified.txt").write_text("content")

        svc = FileOpsService()
        result = svc.rename(
            FileRenameInput(path=tmpdir, strategy=RenameStrategy.SLUGIFY, dry_run=True)
        )
        assert result.skipped_count == 1
        assert result.renamed_count == 0
