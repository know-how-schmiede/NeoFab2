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
    """NeoFab2: Konfiguration, Migration und Betriebsprüfung."""


@main.command("init-config")
@click.option("--output", required=True, type=click.Path(path_type=Path))
@click.option("--data-dir", required=True, type=click.Path(path_type=Path))
def init_config(output, data_dir):
    """Neue Konfiguration anlegen; vorhandene Dateien niemals überschreiben."""
    if not data_dir.is_absolute():
        raise click.ClickException("--data-dir muss absolut sein.")
    content = (
        "# NeoFab2 – nicht in Git aufnehmen.\n"
        f"SECRET_KEY = {json.dumps(secrets.token_hex(32))}\n"
        f"DATA_DIR = {json.dumps(str(data_dir), ensure_ascii=False)}\n"
        "SESSION_COOKIE_SECURE = true\n"
    )
    try:
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
    except OSError as error:
        raise click.ClickException("Konfiguration konnte nicht neu angelegt werden; Pfad und vorhandene Datei prüfen.") from error
    click.echo(f"Konfiguration angelegt: {output}")


def configured_app():
    try:
        return create_app()
    except (OSError, ValueError) as error:
        raise click.ClickException("Konfiguration fehlt oder ist ungültig. NEOFAB2_CONFIG, DATA_DIR und SECRET_KEY prüfen.") from error


@main.command()
def migrate():
    """Versionierte Migrationen bis zum aktuellen Stand ausführen."""
    app = configured_app()
    try:
        upgrade_database(app)
    except Exception as error:
        raise click.ClickException("Migration fehlgeschlagen. Sicherung erhalten und Datenbankzustand prüfen.") from error
    click.echo("Datenbankmigration erfolgreich.")


@main.command()
def check():
    """Datenbank und Schema prüfen; Exit-Code 1 bei fehlender Bereitschaft."""
    app = configured_app()
    if not database_ready(app):
        raise click.ClickException("Datenbank nicht bereit. Pfad, Rechte und 'neofab2 migrate' prüfen.")
    click.echo(f"NeoFab2 {__version__}: Datenbank und Schema bereit.")


@main.command()
@click.option("--output", required=True, type=click.Path(path_type=Path))
def backup(output):
    """Konsistente SQLite-Sicherung erstellen, ohne eine Datei zu überschreiben."""
    app = configured_app()
    if not database_ready(app):
        raise click.ClickException("Datenbank vor Sicherung nicht bereit.")
    source = Path(app.config["DATA_DIR"]) / "neofab2.sqlite3"
    try:
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src:
            with sqlite3.connect(output) as dst:
                src.backup(dst)
                if dst.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise ValueError("Integritätsprüfung fehlgeschlagen")
    except (OSError, sqlite3.Error, ValueError) as error:
        raise click.ClickException("Sicherung fehlgeschlagen; Zieldatei nicht als gültiges Backup verwenden.") from error
    click.echo(f"Datenbank gesichert: {output}")


if __name__ == "__main__":
    main()
