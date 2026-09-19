"""Wartungsbefehle; keine impliziten Schemaänderungen beim Webstart."""

import json
import os
from pathlib import Path
import secrets
import sqlite3

import click

from . import __version__, create_app
from .database import database_ready, upgrade_database


@click.group()
@click.version_option(__version__)
def main():
    """NeoFab2: configuration, migrations and operational checks."""


@main.command("init-config")
@click.option("--output", required=True, type=click.Path(path_type=Path))
@click.option("--data-dir", required=True, type=click.Path(path_type=Path))
@click.option("--http-test", is_flag=True, help="For isolated HTTP test networks only: disable secure cookies.")
def init_config(output, data_dir, http_test):
    """Create a configuration without overwriting existing files."""
    if not data_dir.is_absolute():
        raise click.ClickException("--data-dir must be absolute.")
    content = (
        "# NeoFab2 – do not commit to Git.\n"
        f"SECRET_KEY = {json.dumps(secrets.token_hex(32))}\n"
        f"DATA_DIR = {json.dumps(str(data_dir), ensure_ascii=False)}\n"
        f"SESSION_COOKIE_SECURE = {'false' if http_test else 'true'}\n"
    )
    try:
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
    except OSError as error:
        raise click.ClickException("Could not create configuration; check the path and existing file.") from error
    click.echo(f"Configuration created: {output}")


def configured_app():
    try:
        return create_app()
    except OSError as error:
        raise click.ClickException("Configuration is missing or invalid. Check NEOFAB2_CONFIG, DATA_DIR and SECRET_KEY.") from error
    except ValueError as error:
        raise click.ClickException(str(error)) from error


@main.command("plugins-restore-config")
@click.confirmation_option(prompt="Restore the plugin selection from the server configuration?")
def plugins_restore_config():
    """Recover locally from an invalid saved plugin selection."""
    from .core.plugin_state import restore_config_selection

    app = None
    try:
        app = create_app(use_config_plugins=True)
        if not database_ready(app):
            raise click.ClickException("Database is not ready. Check migrations first.")
        restore_config_selection(app)
    except (OSError, ValueError) as error:
        raise click.ClickException("Plugin recovery failed; check configuration and plugin dependencies.") from error
    finally:
        if app is not None:
            app.extensions["neofab2_db"].dispose()
    click.echo("Plugin selection saved from configuration. Restart all application processes.")


@main.command("plugin-task")
@click.argument("plugin_id")
@click.argument("task_name")
def plugin_task(plugin_id, task_name):
    """Run a task of an enabled plugin locally (operator access)."""
    app = ready_app()
    try:
        with app.app_context():
            result = app.extensions["neofab2_plugins"].run_task(plugin_id, task_name)
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    click.echo(result)


@main.command()
def migrate():
    """Run versioned migrations up to the latest revision."""
    app = configured_app()
    try:
        upgrade_database(app)
    except Exception as error:
        raise click.ClickException("Migration failed. Keep the backup and check the database state.") from error
    click.echo("Database migration completed successfully.")


@main.command()
def check():
    """Check database and schema; exit with code 1 if not ready."""
    app = configured_app()
    if not database_ready(app):
        raise click.ClickException("Database is not ready. Check the path, permissions and 'neofab2 migrate'.")
    click.echo(f"NeoFab2 {__version__}: Database and schema ready.")


@main.command()
@click.option("--output", required=True, type=click.Path(path_type=Path))
def backup(output):
    """Create a consistent SQLite backup without overwriting a file."""
    app = configured_app()
    if not database_ready(app):
        raise click.ClickException("Database is not ready for backup.")
    source = Path(app.config["DATA_DIR"]) / "neofab2.sqlite3"
    try:
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src:
            with sqlite3.connect(output) as dst:
                src.backup(dst)
                if dst.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise ValueError("Integrity check failed")
    except (OSError, sqlite3.Error, ValueError) as error:
        raise click.ClickException("Backup failed; do not use the destination file as a valid backup.") from error
    click.echo(f"Database backed up: {output}")


def ready_app():
    app = configured_app()
    if not database_ready(app):
        raise click.ClickException("Database is not ready. Run 'neofab2 migrate' first.")
    return app


@main.command("create-admin")
@click.option("--email", prompt="First administrator email")
@click.option("--name", prompt="Display name")
def create_admin(email, name):
    """Create the first administrator; no default account or password argument."""
    from .core.users import create_user

    app = ready_app()
    password = click.prompt("Password (8–128 characters)", hide_input=True, confirmation_prompt="Repeat password")
    try:
        create_user(app, email, name, password, role="admin", bootstrap=True)
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    click.echo("First administrator created.")


@main.command("reset-admin-password")
@click.option("--reactivate", is_flag=True, help="Explicitly reactivate the selected disabled administrator account.")
def reset_admin(reactivate):
    """Local emergency access: select an administrator and enter a new password securely."""
    from sqlalchemy import select
    from .core.users import users, PUBLIC_COLUMNS, reset_admin_password

    app = ready_app()
    with app.extensions["neofab2_db"].connect() as connection:
        admins = connection.execute(select(*PUBLIC_COLUMNS).where(users.c.role == "admin").order_by(users.c.id)).mappings().all()
    if not admins:
        raise click.ClickException("No administrator found. Use 'neofab2 create-admin'.")
    for admin in admins:
        click.echo(f"{admin['id']}: {admin['email']} ({'active' if admin['active'] else 'disabled'})")
    selected = click.prompt("Administrator ID", type=click.Choice([str(admin["id"]) for admin in admins]))
    click.confirm("Change this administrator's password and end all their sessions?", abort=True)
    password = click.prompt("New password (8–128 characters)", hide_input=True, confirmation_prompt="Repeat password")
    try:
        reset_admin_password(app, int(selected), password, reactivate=reactivate)
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    click.echo("Administrator password changed; existing sessions ended.")


@main.command("maintenance-info")
def maintenance_info():
    """Read summary information for local operators without loading plugins."""
    from .config import load_config

    click.echo(f"NeoFab2 version: {__version__}")
    try:
        config = load_config()
    except (OSError, ValueError, TypeError):
        raise click.ClickException("Configuration information unavailable.") from None
    if config["SESSION_COOKIE_SECURE"]:
        click.echo("Login: HTTPS required. Use the public HTTPS address of your reverse proxy; this script does not configure TLS.")
    else:
        click.echo("Login: HTTP enabled for an isolated test network.")
    database = Path(config["DATA_DIR"]) / "neofab2.sqlite3"
    try:
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
            admins = connection.execute("SELECT email, active FROM core_users WHERE role = 'admin' ORDER BY id").fetchall()
    except sqlite3.Error:
        click.echo("Administrator emails: unavailable (database or schema not ready).")
        return
    if not admins:
        click.echo("Administrator emails: no administrator account found.")
    for email, active in admins:
        safe_email = "".join(char if char.isprintable() else "?" for char in email)
        click.echo(f"Administrator email: {safe_email} ({'active' if active else 'disabled'})")


if __name__ == "__main__":
    main()
