"""ImageOps CLI subcommands."""

import typer

from gandra_tools.tools.imageops.schemas import DEFAULT_OUTPUT_DIR

imageops_app = typer.Typer(help="Image operations — text extraction, background removal.")


@imageops_app.command("text-extract")
def text_extract(
    image: str = typer.Option(None, "--image", "-i", help="Path to image file or URL"),
    output_dir: str = typer.Option(DEFAULT_OUTPUT_DIR, help="Output directory"),
    file_name: str = typer.Option(None, help="Output file name (without .png)"),
    mode: str = typer.Option("ocr", help="Mode: ocr or mask"),
    language: str = typer.Option("auto", help="OCR language hint (sr, en, auto)"),
    font_color: str = typer.Option("auto", help="Font color: auto, black, #FF0000"),
    min_confidence: float = typer.Option(0.5, help="Min OCR confidence (0.0-1.0)"),
    dpi: int = typer.Option(300, help="Output DPI (72-600)"),
):
    """Extract text from image, output transparent PNG with text only."""
    from gandra_tools.tools.imageops.schemas import ImageExtractMode, ImageTextExtractInput
    from gandra_tools.tools.imageops.service import ImageTextExtractService

    # Interactive mode if no image
    if not image:
        typer.echo("Image Text Extractor")
        typer.echo("-" * 25)
        image = typer.prompt("Image path or URL")
        if not image:
            typer.echo("Image path is required.", err=True)
            raise typer.Exit(1)
        output_dir = typer.prompt("Output folder", default=output_dir)
        file_name = typer.prompt("File name (Enter = auto)", default="") or None
        mode = typer.prompt("Mode (ocr/mask)", default=mode)
        language = typer.prompt("Language", default=language)

    try:
        extract_mode = ImageExtractMode(mode)
    except ValueError:
        typer.echo(f"Unknown mode: {mode}. Use: ocr, mask", err=True)
        raise typer.Exit(1)

    input_data = ImageTextExtractInput(
        image_path=image,
        output_dir=output_dir,
        file_name=file_name,
        mode=extract_mode,
        language=language,
        font_color=font_color,
        min_confidence=min_confidence,
        dpi=dpi,
    )

    service = ImageTextExtractService()
    try:
        result = service.extract(input_data)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"\nSaved: {result.output_path}")
    typer.echo(
        f"{result.regions_detected} regions detected | "
        f"{result.regions_included} included | "
        f"{result.processing_time_ms}ms"
    )
    if result.extracted_text:
        preview = result.extracted_text[:200]
        typer.echo(f'Text: "{preview}{"..." if len(result.extracted_text) > 200 else ""}"')
