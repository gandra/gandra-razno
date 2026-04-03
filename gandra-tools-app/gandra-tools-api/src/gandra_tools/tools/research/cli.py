"""Research CLI subcommands."""

import asyncio

import typer

from gandra_tools.tools.research.schemas import DEFAULT_OUTPUT_DIR

research_app = typer.Typer(help="RAG research — multi-link analysis, credibility, narratives.")


@research_app.command("analyze")
def analyze(
    links: str = typer.Option(None, "--links", "-l", help="Comma-separated URLs"),
    file: str = typer.Option(None, "--file", "-f", help="File with URLs (one per line)"),
    depth: str = typer.Option("medium", help="Analysis depth: shallow, medium, deep"),
    focus: str = typer.Option("all", help="Focus: all, credibility, narrative, summary, fact_check"),
    language: str = typer.Option("sr", help="Output language (sr, en)"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, help="Output directory"),
    file_name: str = typer.Option(None, help="Output file name"),
    fmt: str = typer.Option("md", "--format", help="Output format"),
):
    """Analyze articles/news from multiple links with AI."""
    from pathlib import Path

    from gandra_tools.models.schemas import OutputFormat
    from gandra_tools.tools.research.schemas import AnalysisDepth, AnalysisFocus, ResearchAnalysisInput
    from gandra_tools.tools.research.service import ResearchService

    # Gather links
    url_list: list[str] = []
    if file:
        path = Path(file)
        if not path.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(1)
        url_list = [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    elif links:
        url_list = [u.strip() for u in links.split(",") if u.strip()]
    else:
        # Interactive mode
        typer.echo("RAG Research Analyzer")
        typer.echo("-" * 25)
        typer.echo("Enter URLs (one per line, empty line to finish):")
        while True:
            url = typer.prompt("URL", default="")
            if not url:
                break
            url_list.append(url)
        if not url_list:
            typer.echo("At least one URL is required.", err=True)
            raise typer.Exit(1)
        depth = typer.prompt("Depth (shallow/medium/deep)", default=depth)
        fmt = typer.prompt("Format (md/json/txt/html)", default=fmt)

    try:
        analysis_depth = AnalysisDepth(depth)
    except ValueError:
        typer.echo(f"Unknown depth: {depth}", err=True)
        raise typer.Exit(1)

    try:
        output_format = OutputFormat(fmt)
    except ValueError:
        typer.echo(f"Unknown format: {fmt}", err=True)
        raise typer.Exit(1)

    focus_list = [AnalysisFocus(f.strip()) for f in focus.split(",")]

    input_data = ResearchAnalysisInput(
        links=url_list,
        depth=analysis_depth,
        focus=focus_list,
        language=language,
        output_dir=output_dir,
        file_name=file_name,
        output_format=output_format,
    )

    typer.echo(f"Analyzing {len(url_list)} source(s) at depth={depth}...")

    service = ResearchService()
    try:
        result = asyncio.run(service.analyze(input_data))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"\nSaved: {result.file_path}")
    typer.echo(f"Sources: {result.sources_analyzed} | Confidence: {result.confidence_score:.0%}")
    typer.echo(f"Summary: {result.executive_summary[:200]}...")
