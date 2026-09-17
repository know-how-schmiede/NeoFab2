"""SQLite-Basis und explizite Alembic-Migrationen (X07)."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, URL, text
from sqlalchemy.exc import SQLAlchemyError


def migration_config():
    from . import migrations

    config = Config()
    config.set_main_option("script_location", str(Path(migrations.__file__).parent).replace("%", "%%"))
    return config


def init_database(app):
    # Engine creation opens no connection and creates neither directory nor schema.
    path = Path(app.config["DATA_DIR"]) / "neofab2.sqlite3"
    app.extensions["neofab2_db"] = create_engine(
        URL.create("sqlite", database=str(path)),
        connect_args={"timeout": 15},
    )


def upgrade_database(app):
    Path(app.config["DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    config = migration_config()
    with app.extensions["neofab2_db"].begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def database_ready(app):
    if not (Path(app.config["DATA_DIR"]) / "neofab2.sqlite3").is_file():
        return False
    try:
        with app.extensions["neofab2_db"].connect() as connection:
            expected = set(ScriptDirectory.from_config(migration_config()).get_heads())
            actual = set(MigrationContext.configure(connection).get_current_heads())
            connection.execute(text("SELECT key, value FROM core_settings LIMIT 0"))
            return actual == expected
    except SQLAlchemyError:
        return False
