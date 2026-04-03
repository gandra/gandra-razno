"""YouTube CLI subcommands."""

import typer

from gandra_tools.tools.youtube.schemas import DEFAULT_OUTPUT_DIR

youtube_app = typer.Typer(help="YouTube transcript and media tools.")


@youtube_app.command("transcript")
def transcript(
    url: str = typer.Option(None, help="YouTube video URL"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, help="Output directory"),
    file_name: str = typer.Option(None, help="Output file name (without extension)"),
    interval: int = typer.Option(2, help="Group segments by N minutes"),
    language: str = typer.Option("auto", help="Transcript language (sr, en, auto)"),
    fmt: str = typer.Option("md", "--format", help="Output format (md, json, txt, html)"),
):
    """Extract transcript from a YouTube video with timestamps."""
    from gandra_tools.models.schemas import OutputFormat
    from gandra_tools.tools.youtube.schemas import TranscriptInput
    from gandra_tools.tools.youtube.service import YouTubeTranscriptService

    # Interactive mode if no URL
    if not url:
        typer.echo("YouTube Transcript Extractor")
        typer.echo("-" * 35)
        url = typer.prompt("YouTube URL")
        if not url:
            typer.echo("URL is required.", err=True)
            raise typer.Exit(1)
        output_dir = typer.prompt("Output folder", default=output_dir)
        file_name = typer.prompt("File name (Enter = auto)", default="") or None
        interval = int(typer.prompt("Interval (min)", default=str(interval)))
        fmt = typer.prompt("Format (md/json/txt/html)", default=fmt)

    try:
        output_format = OutputFormat(fmt)
    except ValueError:
        typer.echo(f"Unknown format: {fmt}. Use: md, json, txt, html", err=True)
        raise typer.Exit(1)

    input_data = TranscriptInput(
        url=url,
        output_dir=output_dir,
        file_name=file_name,
        interval_minutes=interval,
        language=language,
        output_format=output_format,
    )

    service = YouTubeTranscriptService()
    try:
        result = service.extract(input_data)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"\nSaved: {result.file_path}")
    typer.echo(f"{result.duration_formatted} | {result.segment_count} segments | {result.word_count} words")
