"""DevTools CLI subcommands."""

import asyncio

import typer

devtools_app = typer.Typer(help="Developer tools — API testing and code review.")


@devtools_app.command("api-test")
def api_test(
    method: str = typer.Argument("GET", help="HTTP method"),
    url: str = typer.Argument(..., help="URL to test"),
    expected: int = typer.Option(None, "--expected", "-e", help="Expected status code"),
    repeat: int = typer.Option(1, "--repeat", "-r", help="Number of requests"),
    timeout: int = typer.Option(30, help="Timeout in seconds"),
    header: list[str] = typer.Option([], "--header", "-H", help="Headers (Key: Value)"),
):
    """Test an HTTP API endpoint."""
    from gandra_tools.tools.devtools.schemas import ApiTestInput, HttpMethod
    from gandra_tools.tools.devtools.service import ApiTestService

    try:
        http_method = HttpMethod(method.upper())
    except ValueError:
        typer.echo(f"Invalid method: {method}", err=True)
        raise typer.Exit(1)

    headers = {}
    for h in header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()

    input_data = ApiTestInput(
        method=http_method,
        url=url,
        headers=headers or None,
        expected_status=expected,
        timeout_seconds=timeout,
        repeat=repeat,
    )

    service = ApiTestService()
    try:
        result = asyncio.run(service.test(input_data))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    status = "PASS" if result.all_passed else "FAIL"
    typer.echo(f"[{status}] {result.method} {result.url}")
    typer.echo(f"Avg response: {result.avg_response_time_ms}ms | Requests: {result.repeat_count}")

    for i, r in enumerate(result.results, 1):
        mark = "✓" if r.success else "✗"
        typer.echo(f"  {mark} #{i}: {r.status_code} ({r.response_time_ms}ms, {r.body_size_bytes}B)")


@devtools_app.command("code-review")
def code_review(
    path: str = typer.Argument(..., help="File or directory to review"),
    focus: str = typer.Option("bugs,security,performance", help="Focus areas (comma-separated)"),
    max_files: int = typer.Option(10, help="Max files to review"),
    fmt: str = typer.Option("md", "--format", help="Output format"),
):
    """AI-powered code review."""
    from gandra_tools.models.schemas import OutputFormat
    from gandra_tools.tools.devtools.schemas import CodeReviewInput
    from gandra_tools.tools.devtools.service import CodeReviewService

    try:
        output_format = OutputFormat(fmt)
    except ValueError:
        typer.echo(f"Unknown format: {fmt}", err=True)
        raise typer.Exit(1)

    input_data = CodeReviewInput(
        path=path,
        focus=[f.strip() for f in focus.split(",")],
        max_files=max_files,
        output_format=output_format,
    )

    service = CodeReviewService()
    try:
        result = asyncio.run(service.review(input_data))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Reviewed {result.files_reviewed} file(s) | {result.total_findings} finding(s)")
    if result.file_path:
        typer.echo(f"Report: {result.file_path}")

    for f in result.findings:
        icon = {"critical": "🔴", "error": "🟠", "warning": "🟡", "info": "🔵"}.get(f.severity, "⚪")
        loc = f":{f.line}" if f.line else ""
        typer.echo(f"  {icon} [{f.severity}] {f.file}{loc} — {f.message}")
