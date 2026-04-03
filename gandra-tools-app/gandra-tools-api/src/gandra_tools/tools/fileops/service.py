"""File operations service — search and batch rename."""

import re
from datetime import date, datetime, timezone
from pathlib import Path

from gandra_tools.tools.fileops.schemas import (
    FileRenameInput,
    FileRenameOutput,
    FileSearchInput,
    FileSearchOutput,
    FileSearchResult,
    RenamePreview,
    RenameStrategy,
)


def _apply_strategy(name: str, strategy: RenameStrategy, **opts) -> str:
    """Apply rename strategy to a filename (without extension)."""
    stem = Path(name).stem
    ext = Path(name).suffix

    if strategy == RenameStrategy.SLUGIFY:
        result = re.sub(r"[^\w\s-]", "", stem.lower())
        result = re.sub(r"[\s_]+", "-", result).strip("-")
        result = re.sub(r"-+", "-", result)
    elif strategy == RenameStrategy.UPPERCASE:
        result = stem.upper()
    elif strategy == RenameStrategy.LOWERCASE:
        result = stem.lower()
    elif strategy == RenameStrategy.SNAKE_CASE:
        result = re.sub(r"[\s\-]+", "_", stem)
        result = re.sub(r"([a-z])([A-Z])", r"\1_\2", result).lower()
        result = re.sub(r"_+", "_", result).strip("_")
    elif strategy == RenameStrategy.KEBAB_CASE:
        result = re.sub(r"[\s_]+", "-", stem)
        result = re.sub(r"([a-z])([A-Z])", r"\1-\2", result).lower()
        result = re.sub(r"-+", "-", result).strip("-")
    elif strategy == RenameStrategy.CAMEL_CASE:
        words = re.split(r"[\s_\-]+", stem)
        result = words[0].lower() + "".join(w.capitalize() for w in words[1:]) if words else stem
    elif strategy == RenameStrategy.PREFIX:
        prefix = opts.get("prefix", "")
        result = f"{prefix}{stem}"
    elif strategy == RenameStrategy.SUFFIX:
        suffix = opts.get("suffix", "")
        result = f"{stem}{suffix}"
    elif strategy == RenameStrategy.DATE_PREFIX:
        result = f"{date.today():%Y-%m-%d}_{stem}"
    elif strategy == RenameStrategy.REGEX:
        pattern = opts.get("pattern", "")
        replacement = opts.get("replacement", "")
        result = re.sub(pattern, replacement, stem) if pattern else stem
    else:
        result = stem

    return f"{result}{ext}"


class FileOpsService:
    """File search and batch rename operations."""

    def search(self, input_data: FileSearchInput) -> FileSearchOutput:
        """Search files by name pattern and optionally by content."""
        root = Path(input_data.path)
        if not root.exists():
            raise ValueError(f"Directory does not exist: {input_data.path}")
        if not root.is_dir():
            raise ValueError(f"Not a directory: {input_data.path}")

        glob_method = root.rglob if input_data.recursive else root.glob
        results: list[FileSearchResult] = []

        content_regex = None
        if input_data.content:
            content_regex = re.compile(input_data.content, re.IGNORECASE)

        for filepath in glob_method(input_data.pattern):
            if not filepath.is_file():
                continue
            if not input_data.include_hidden and filepath.name.startswith("."):
                continue

            content_match = None
            if content_regex:
                try:
                    text = filepath.read_text(encoding="utf-8", errors="ignore")
                    match = content_regex.search(text)
                    if not match:
                        continue
                    # Extract matching line
                    line_start = text.rfind("\n", 0, match.start()) + 1
                    line_end = text.find("\n", match.end())
                    content_match = text[line_start : line_end if line_end > 0 else None].strip()[:200]
                except Exception:
                    continue

            stat = filepath.stat()
            results.append(
                FileSearchResult(
                    path=str(filepath),
                    name=filepath.name,
                    size_bytes=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    content_match=content_match,
                )
            )

            if len(results) >= input_data.max_results:
                break

        return FileSearchOutput(
            query_path=input_data.path,
            pattern=input_data.pattern,
            content_query=input_data.content,
            total_found=len(results),
            results=results,
        )

    def rename(self, input_data: FileRenameInput) -> FileRenameOutput:
        """Batch rename files with the specified strategy."""
        root = Path(input_data.path)
        if not root.exists():
            raise ValueError(f"Directory does not exist: {input_data.path}")

        glob_method = root.rglob if input_data.recursive else root.glob
        previews: list[RenamePreview] = []
        renamed_count = 0
        skipped_count = 0

        opts = {
            "prefix": input_data.prefix or "",
            "suffix": input_data.suffix or "",
            "pattern": input_data.pattern or "",
            "replacement": input_data.replacement or "",
        }

        for filepath in sorted(glob_method(input_data.file_pattern)):
            if not filepath.is_file():
                continue

            new_name = _apply_strategy(filepath.name, input_data.strategy, **opts)

            if new_name == filepath.name:
                previews.append(RenamePreview(original=filepath.name, renamed=new_name, status="skipped"))
                skipped_count += 1
                continue

            new_path = filepath.parent / new_name

            if input_data.dry_run:
                previews.append(RenamePreview(original=filepath.name, renamed=new_name, status="pending"))
            else:
                try:
                    if new_path.exists():
                        previews.append(
                            RenamePreview(original=filepath.name, renamed=new_name, status="skipped")
                        )
                        skipped_count += 1
                        continue
                    filepath.rename(new_path)
                    previews.append(RenamePreview(original=filepath.name, renamed=new_name, status="renamed"))
                    renamed_count += 1
                except Exception as e:
                    previews.append(
                        RenamePreview(original=filepath.name, renamed=new_name, status=f"error: {e}")
                    )

        if input_data.dry_run:
            renamed_count = sum(1 for p in previews if p.status == "pending")

        return FileRenameOutput(
            strategy=input_data.strategy,
            dry_run=input_data.dry_run,
            total_files=len(previews),
            renamed_count=renamed_count,
            skipped_count=skipped_count,
            previews=previews,
        )
