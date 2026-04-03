"""Typer CLI entry point with tool autodiscovery."""

import importlib
import pkgutil

import typer

app = typer.Typer(
    name="gandra-tools",
    help="Swiss-army toolset — YouTube transcripts, RAG research, file ops, and more.",
    no_args_is_help=True,
)


# ── Tool subcommand autodiscovery ────────────────────────────
def _discover_tool_cli_apps() -> None:
    """Scan tools/ subpackages for cli.py modules with a Typer app."""
    try:
        import gandra_tools.tools as tools_pkg
    except ImportError:
        return

    for _importer, module_name, is_pkg in pkgutil.iter_modules(tools_pkg.__path__):
        if not is_pkg:
            continue
        try:
            cli_mod = importlib.import_module(f"gandra_tools.tools.{module_name}.cli")
        except ImportError:
            continue

        # Convention: cli.py exports a Typer app named <tool_name>_app
        for attr_name in dir(cli_mod):
            attr = getattr(cli_mod, attr_name)
            if isinstance(attr, typer.Typer) and attr is not app:
                app.add_typer(attr, name=module_name)
                break


_discover_tool_cli_apps()


# ── Publish command ──────────────────────────────────────────
publish_app = typer.Typer(help="Publish content in various formats.")
app.add_typer(publish_app, name="publish")


@publish_app.command("file")
def publish_file(
    input_path: str = typer.Argument(..., help="Path to JSON file with content"),
    fmt: str = typer.Option("md", "--format", "-f", help="Output format (md, json, txt, html, facebook, linkedin, instagram, x)"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    content_type: str = typer.Option("generic", "--type", "-t", help="Content type for template selection"),
):
    """Publish a JSON file to another format."""
    import json
    from pathlib import Path

    from gandra_tools.core.publisher.schemas import PublishRequest
    from gandra_tools.core.publisher.service import PublisherService
    from gandra_tools.models.schemas import OutputFormat

    path = Path(input_path)
    if not path.exists():
        typer.echo(f"File not found: {input_path}", err=True)
        raise typer.Exit(1)

    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    try:
        output_format = OutputFormat(fmt)
    except ValueError:
        typer.echo(f"Unknown format: {fmt}. Available: {', '.join(f.value for f in OutputFormat)}", err=True)
        raise typer.Exit(1)

    if not output:
        output = str(path.with_suffix(f".{fmt}"))

    publisher = PublisherService()
    resp = publisher.publish(
        PublishRequest(content=content, content_type=content_type, format=output_format, output_path=output)
    )
    typer.echo(f"Published: {resp.file_path} ({resp.size_bytes} bytes)")


@publish_app.command("formats")
def publish_formats():
    """List all supported output formats."""
    from gandra_tools.core.publisher.service import PublisherService

    for fmt in PublisherService.get_supported_formats():
        typer.echo(f"  {fmt}")


# ── Auth commands ────────────────────────────────────────────
auth_app = typer.Typer(help="Authentication commands.")
app.add_typer(auth_app, name="auth")


@auth_app.command("change-password")
def change_password(
    current: str = typer.Option(..., prompt=True, hide_input=True, help="Current password"),
    new: str = typer.Option(
        ..., prompt=True, hide_input=True, confirmation_prompt=True, help="New password"
    ),
):
    """Change password for the default user."""
    from gandra_tools.core.auth import hash_password
    from gandra_tools.core.config import get_settings

    settings = get_settings()

    if current != settings.default_user_password:
        typer.echo("Current password is incorrect.", err=True)
        raise typer.Exit(1)

    _new_hash = hash_password(new)
    typer.echo("Password changed successfully.")


# ── Config commands ──────────────────────────────────────────
config_app = typer.Typer(help="Settings management.")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show(category: str = typer.Option(None, help="Filter by category")):
    """Show all settings with resolved values and source."""
    from gandra_tools.core.config import get_settings
    from gandra_tools.core.settings_service import SettingsService

    settings = get_settings()
    svc = SettingsService()
    all_settings = svc.list_all(user_id=settings.default_user_email)

    typer.echo(f"{'Key':<30} {'Value':<20} {'Source':<10}")
    typer.echo("-" * 60)
    for key, info in sorted(all_settings.items()):
        if category and not key.startswith(category):
            continue
        val = str(info["value"]) if info["value"] is not None else "(none)"
        typer.echo(f"{key:<30} {val:<20} {info['source']:<10}")


@config_app.command("set")
def config_set(key: str, value: str, is_global: bool = typer.Option(False, "--global")):
    """Set a setting value."""
    from gandra_tools.core.config import get_settings
    from gandra_tools.core.settings_service import SettingsService

    settings = get_settings()
    svc = SettingsService()
    if is_global:
        svc.set_global(key, value)
    else:
        svc.set_user(settings.default_user_email, key, value)
    typer.echo(f"Set {key} = {value}")


# ── Env commands ─────────────────────────────────────────────
env_app = typer.Typer(help="Environment management.")
app.add_typer(env_app, name="env")


@env_app.command("list")
def env_list():
    """List all environments."""
    typer.echo("Environments (from codebook — DB required):")
    typer.echo("  Run the API server first, then use: gandra-tools env list")
    typer.echo("  (Phase 2: DB-backed environment management)")


@env_app.command("current")
def env_current():
    """Show the active environment."""
    from gandra_tools.core.settings_service import SettingsService

    svc = SettingsService()
    active = svc.get_active_env()
    if active:
        typer.echo(f"Active environment: {active}")
    else:
        typer.echo("No active environment set.")


@env_app.command("set")
def env_set(slug: str):
    """Set the active environment."""
    from gandra_tools.core.settings_service import SettingsService

    svc = SettingsService()
    svc.set_active_env(slug)
    typer.echo(f"Active environment: {slug}")
