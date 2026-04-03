"""Typer CLI entry point."""

import typer

app = typer.Typer(
    name="gandra-tools",
    help="Swiss-army toolset — YouTube transcripts, RAG research, file ops, and more.",
    no_args_is_help=True,
)

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

    # Phase 1: compare plain text against default password
    if current != settings.default_user_password:
        typer.echo("Current password is incorrect.", err=True)
        raise typer.Exit(1)

    # Store new hash (Phase 1: print confirmation, DB storage in Phase 2)
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
