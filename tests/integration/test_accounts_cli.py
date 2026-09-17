"""X04/X07: Erstadmin, Notfall-Reset und Migration des vorherigen Schemas."""

import sqlite3

from alembic import command
from click.testing import CliRunner
from sqlalchemy import select, update
from werkzeug.security import check_password_hash

from neofab2 import create_app
from neofab2.cli import main
from neofab2.database import migration_config, upgrade_database, database_ready
from neofab2.core.auth import authenticate
from neofab2.core.users import users, sessions

PASSWORD = "Synthetic initial password!"
RESET_PASSWORD = "Synthetic reset password!"


def test_migrate_previous_schema_without_data_loss(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "x" * 64, "DATA_DIR": str(tmp_path)})
    try:
        config = migration_config()
        with app.extensions["neofab2_db"].begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0001_core_settings")
        with sqlite3.connect(tmp_path / "neofab2.sqlite3") as db:
            db.execute("INSERT INTO core_settings VALUES ('example', 'retained')")
        assert not database_ready(app)
        upgrade_database(app)
        assert database_ready(app)
        with sqlite3.connect(tmp_path / "neofab2.sqlite3") as db:
            assert db.execute("SELECT value FROM core_settings").fetchone() == ("retained",)
            assert db.execute("SELECT count(*) FROM core_users").fetchone() == (0,)
    finally:
        app.extensions["neofab2_db"].dispose()


def test_cli_first_admin_reset_and_reactivation(tmp_path, monkeypatch):
    runner = CliRunner()
    config = tmp_path / "config.toml"
    assert runner.invoke(main, ["init-config", "--output", str(config), "--data-dir", str(tmp_path), "--http-test"]).exit_code == 0
    monkeypatch.setenv("NEOFAB2_CONFIG", str(config))
    assert runner.invoke(main, ["create-admin", "--email", "admin@example.org", "--name", "Admin"]).exit_code == 1
    assert runner.invoke(main, ["migrate"]).exit_code == 0
    assert runner.invoke(main, ["reset-admin-password"]).exit_code == 1
    args = ["create-admin", "--email", "admin@example.org", "--name", "Admin"]
    result = runner.invoke(main, args, input=f"{PASSWORD}\n{PASSWORD}\n")
    assert result.exit_code == 0, result.output
    assert PASSWORD not in result.output
    assert runner.invoke(main, args, input=f"{PASSWORD}\n{PASSWORD}\n").exit_code == 1
    app = create_app()
    try:
        token = authenticate(app, "admin@example.org", PASSWORD, "127.0.0.1")
        assert token
        result = runner.invoke(main, ["reset-admin-password"], input=f"1\ny\n{RESET_PASSWORD}\n{RESET_PASSWORD}\n")
        assert result.exit_code == 0, result.output
        assert RESET_PASSWORD not in result.output
        with app.extensions["neofab2_db"].begin() as connection:
            assert not connection.execute(select(sessions)).first()
            assert check_password_hash(connection.execute(select(users.c.password_hash)).scalar_one(), RESET_PASSWORD)
            connection.execute(update(users).values(active=False))
        answer = f"1\ny\n{PASSWORD}\n{PASSWORD}\n"
        assert runner.invoke(main, ["reset-admin-password"], input=answer).exit_code == 1
        result = runner.invoke(main, ["reset-admin-password", "--reactivate"], input=answer)
        assert result.exit_code == 0, result.output
        assert authenticate(app, "admin@example.org", PASSWORD, "127.0.0.1")
    finally:
        app.extensions["neofab2_db"].dispose()
