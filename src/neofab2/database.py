"""SQLite-Basis und explizite Alembic-Migrationen (X07)."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, URL, text, event
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

    @event.listens_for(app.extensions["neofab2_db"], "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")


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
            connection.execute(text("SELECT id, email, display_name, password_hash, role, active, created_at, theme, locale FROM core_users LIMIT 0"))
            connection.execute(text("SELECT salutation, first_name, last_name, address, position, cost_center, study_program, note FROM core_users LIMIT 0"))
            connection.execute(text("SELECT token_hash, user_id, created_at, last_seen FROM core_sessions LIMIT 0"))
            connection.execute(text("SELECT key, count, window_start FROM core_login_attempts LIMIT 0"))
            connection.execute(text("SELECT id, kind, name, active FROM core_user_options LIMIT 0"))
            connection.execute(text("SELECT id, plugin_id, owner_id, filename, size, created_at, content FROM core_files LIMIT 0"))
            connection.execute(text("SELECT id, status, lease_token, next_attempt_at FROM core_mail_outbox LIMIT 0"))
            connection.execute(text("SELECT activation_pending FROM core_users LIMIT 0"))
            connection.execute(text("SELECT id, user_id, purpose, token_hash, fingerprint, expires_at, used_at FROM core_account_tokens LIMIT 0"))
            connection.execute(text("SELECT key, count, window_start FROM core_account_limits LIMIT 0"))
            connection.execute(text("SELECT account_user_id, account_token_id FROM core_mail_outbox LIMIT 0"))
            connection.execute(text("SELECT id, created_at, module_id, event, actor_id, target_id, count FROM core_audit_events LIMIT 0"))
            connection.execute(text("SELECT name, run_id, started_at, finished_at, state FROM core_worker_status LIMIT 0"))
            return actual == expected
    except SQLAlchemyError:
        return False
