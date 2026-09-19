"""S01/S12/X07: Start ohne Fachplugins, Migration und Bereitschaft."""

import sqlite3

import pytest

from neofab2 import __version__, create_app
from neofab2.database import upgrade_database


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    application = create_app({"TESTING": True, "SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path / "data")})
    yield application
    application.extensions["neofab2_db"].dispose()


def test_start_and_requests_never_create_schema(app):
    from pathlib import Path

    client = app.test_client()
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 503
    assert client.get("/").status_code == 503
    assert not Path(app.config["DATA_DIR"]).exists()


def test_explicit_migration_is_repeatable_and_preserves_data(app):
    from pathlib import Path

    upgrade_database(app)
    path = Path(app.config["DATA_DIR"]) / "neofab2.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO core_settings VALUES (?, ?)", ("test.setting", "synthetic"))
    upgrade_database(app)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT value FROM core_settings").fetchone() == ("synthetic",)
        assert {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")} == {
            "core_settings", "alembic_version", "core_users", "core_sessions", "core_login_attempts", "core_user_options"}
    client = app.test_client()
    assert client.get("/health/ready").json == {"status": "ok"}
    page = client.get("/")
    assert page.status_code == 200
    assert __version__.encode() in page.data
    assert "Core ready" in page.text
    assert client.get("/static/branding/neofab2-logo.png").status_code == 200
    assert client.get("/static/core.css").status_code == 200
    assert "frame-ancestors 'none'" in page.headers["Content-Security-Policy"]


@pytest.mark.parametrize("corruption", ["DELETE FROM alembic_version", "UPDATE alembic_version SET version_num='unknown'", "DROP TABLE core_settings"])
def test_invalid_schema_fails_readiness(app, corruption):
    from pathlib import Path

    upgrade_database(app)
    with sqlite3.connect(Path(app.config["DATA_DIR"]) / "neofab2.sqlite3") as db:
        db.execute(corruption)
    assert app.test_client().get("/health/ready").status_code == 503


def test_factories_do_not_share_database(app, tmp_path):
    upgrade_database(app)
    other = create_app({"TESTING": True, "SECRET_KEY": "x" * 64, "DATA_DIR": str(tmp_path / "other")})
    try:
        assert other.test_client().get("/health/ready").status_code == 503
        assert app.test_client().get("/health/ready").status_code == 200
    finally:
        other.extensions["neofab2_db"].dispose()


@pytest.mark.parametrize("secret", [None, "short", 123])
def test_unsafe_secret_rejected(secret, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app({"SECRET_KEY": secret})
