"""FileOps CLI subcommands."""

import typer

fileops_app = typer.Typer(help="File operations — search and batch rename.")


@fileops_app.command("search")
def search(
    path: str = typer.Argument(..., help="Directory to search"),
    pattern: str = typer.Option("*", "--pattern", "-p", help="Glob pattern"),
    content: str = typer.Option(None, "--content", "-c", help="Search file content (regex)"),
    recursive: bool = typer.Option(True, help="Search recursively"),
    max_results: int = typer.Option(50, "--max", help="Max results"),
):
    """Search files by name and content."""
    from gandra_tools.tools.fileops.schemas import FileSearchInput
    from gandra_tools.tools.fileops.service import FileOpsService

    input_data = FileSearchInput(
        path=path, pattern=pattern, content=content, recursive=recursive, max_results=max_results
    )

    try:
        result = FileOpsService().search(input_data)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Found {result.total_found} file(s) in {result.query_path}")
    for r in result.results:
        line = f"  {r.name}  ({r.size_bytes} bytes)"
        if r.content_match:
            line += f"  >> {r.content_match[:80]}"
        typer.echo(line)


@fileops_app.command("rename")
def rename(
    path: str = typer.Argument(..., help="Directory with files"),
    strategy: str = typer.Option(..., "--strategy", "-s", help="slugify, uppercase, lowercase, snake_case, kebab-case, camelCase, prefix, suffix, regex, date_prefix"),
    prefix: str = typer.Option(None, help="Prefix string (for prefix strategy)"),
    suffix: str = typer.Option(None, help="Suffix string (for suffix strategy)"),
    pattern: str = typer.Option(None, "--regex-pattern", help="Regex pattern (for regex strategy)"),
    replacement: str = typer.Option(None, "--regex-replace", help="Regex replacement"),
    file_pattern: str = typer.Option("*", "--files", "-f", help="Glob pattern to select files"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Preview or execute"),
):
    """Batch rename files with various strategies."""
    from gandra_tools.tools.fileops.schemas import FileRenameInput, RenameStrategy
    from gandra_tools.tools.fileops.service import FileOpsService

    try:
        rename_strategy = RenameStrategy(strategy)
    except ValueError:
        typer.echo(f"Unknown strategy: {strategy}. Available: {', '.join(s.value for s in RenameStrategy)}", err=True)
        raise typer.Exit(1)

    input_data = FileRenameInput(
        path=path,
        strategy=rename_strategy,
        prefix=prefix,
        suffix=suffix,
        pattern=pattern,
        replacement=replacement,
        file_pattern=file_pattern,
        dry_run=dry_run,
    )

    try:
        result = FileOpsService().rename(input_data)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    mode = "DRY RUN" if result.dry_run else "EXECUTED"
    typer.echo(f"[{mode}] Strategy: {result.strategy.value} | Files: {result.total_files} | Renamed: {result.renamed_count} | Skipped: {result.skipped_count}")
    for p in result.previews:
        if p.original != p.renamed:
            typer.echo(f"  {p.original} → {p.renamed}  [{p.status}]")
