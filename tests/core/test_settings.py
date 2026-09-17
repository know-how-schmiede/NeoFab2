"""S04/U07: persistente Einstellungen, Rechte und Migration mit Testdaten."""

import re
import sqlite3

from alembic import command
import pytest
from sqlalchemy import select, update

from neofab2 import create_app
from neofab2.database import database_ready, migration_config, upgrade_database
from neofab2.core.settings import DEFAULTS, read_settings, save_settings, settings
from neofab2.core.users import create_user, users


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"TESTING": True, "SECRET_KEY": "s" * 64,
                      "DATA_DIR": str(tmp_path), "SESSION_COOKIE_SECURE": False})
    upgrade_database(app)
    admin = create_user(app, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    for role in ("user", "staff"):
        create_user(app, f"{role}@example.org", role, "Test123!", role, actor_id=admin)
    yield app
    app.extensions["neofab2_db"].dispose()


def post(client, path, values, form=None):
    page = client.get(form or path)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    return client.post(path, data={**values, "csrf_token": token})


def login(client, role="admin"):
    assert post(client, "/login", {"email": f"{role}@example.org", "password": "Test123!"}).status_code == 302


def test_settings_rights_csrf_and_persistence(app):
    assert app.test_client().get("/admin/settings").location == "/login"
    for role in ("user", "staff"):
        client = app.test_client()
        login(client, role)
        assert client.get("/admin/settings").status_code == 403
        assert "/admin/settings" not in client.get("/profile").text
        assert post(client, "/admin/settings", DEFAULTS, form="/profile").status_code == 403
    client = app.test_client()
    login(client)
    assert client.post("/admin/settings", data=DEFAULTS).status_code == 400
    assert read_settings(app) == DEFAULTS
    values = {**DEFAULTS, "site_name": "Testwerkstatt", "welcome_text": "Test\nBegrüßung", "default_theme": "light"}
    assert post(client, "/admin/settings", values).status_code == 302
    other = create_app({key: app.config[key] for key in ("SECRET_KEY", "DATA_DIR", "SESSION_COOKIE_SECURE")})
    try:
        page = other.test_client().get("/")
        assert "Testwerkstatt" in page.text and 'data-theme="light"' in page.text
        assert read_settings(other) == values
    finally:
        other.extensions["neofab2_db"].dispose()


@pytest.mark.parametrize("patch", [
    {"site_name": ""}, {"site_name": "x" * 81}, {"site_tagline": "x" * 161},
    {"welcome_text": "x" * 2001}, {"default_theme": "invalid"}, {"SECRET_KEY": "injected"},
])
def test_invalid_settings_atomic_and_no_secret_edit(app, patch):
    client = app.test_client()
    login(client)
    assert post(client, "/admin/settings", {**DEFAULTS, **patch}).status_code == 400
    assert read_settings(app) == DEFAULTS
    assert app.config["SECRET_KEY"] == "s" * 64


def test_public_values_escaped_and_private_settings_not_exposed(app):
    with app.extensions["neofab2_db"].begin() as conn:
        conn.execute(settings.insert().values(key="smtp.password", value="never-public-secret"))
    client = app.test_client()
    login(client)
    assert post(client, "/admin/settings", {**DEFAULTS, "site_name": '<script>alert("x")</script>'}).status_code == 302
    page = app.test_client().get("/")
    assert "<script>" not in page.text and "&lt;script&gt;" in page.text
    assert "never-public-secret" not in page.text
    assert "never-public-secret" not in client.get("/admin/settings").text
    with app.extensions["neofab2_db"].connect() as conn:
        assert conn.execute(select(settings.c.value).where(settings.c.key == "smtp.password")).scalar_one() == "never-public-secret"


def test_profile_theme_own_only_and_survives_login(app):
    client = app.test_client()
    login(client, "user")
    assert post(client, "/profile", {"display_name": "User", "theme": "light", "id": "1", "role": "admin"}).status_code == 302
    assert 'data-theme="light"' in client.get("/profile").text
    with app.extensions["neofab2_db"].connect() as conn:
        rows = conn.execute(select(users.c.role, users.c.theme)).all()
    assert ("admin", "system") in rows and ("user", "light") in rows
    new_client = app.test_client()
    login(new_client, "user")
    assert 'data-theme="light"' in new_client.get("/profile").text
    assert post(new_client, "/profile", {"display_name": "Wrong", "theme": "invalid"}).status_code == 400
    assert 'data-theme="light"' in new_client.get("/profile").text
    save_settings(app, 1, {**DEFAULTS, "default_theme": "dark"})
    assert 'data-theme="light"' in new_client.get("/profile").text
    assert post(new_client, "/profile", {"display_name": "User", "theme": "system"}).status_code == 302
    assert 'data-theme="dark"' in new_client.get("/profile").text


def test_settings_recheck_revoked_actor(app):
    with app.extensions["neofab2_db"].begin() as conn:
        conn.execute(update(users).where(users.c.id == 1).values(active=False))
    with pytest.raises(PermissionError):
        save_settings(app, 1, DEFAULTS)


def test_migrate_013_retains_user_hash_and_setting(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path)})
    try:
        config = migration_config()
        with app.extensions["neofab2_db"].begin() as conn:
            config.attributes["connection"] = conn
            command.upgrade(config, "0002_core_users")
        with sqlite3.connect(tmp_path / "neofab2.sqlite3") as conn:
            conn.execute("INSERT INTO core_users (email, display_name, password_hash, role, active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                         ("old@example.org", "Existing", "synthetic-hash-retained", "admin", 1, 123))
            conn.execute("INSERT INTO core_settings VALUES ('unrelated', 'retained')")
        assert not database_ready(app)
        assert app.test_client().get("/login").status_code == 503
        upgrade_database(app)
        upgrade_database(app)
        assert database_ready(app)
        with app.extensions["neofab2_db"].connect() as conn:
            row = conn.execute(select(users)).mappings().one()
            assert row["theme"] == "system" and row["password_hash"] == "synthetic-hash-retained"
            assert conn.execute(select(settings.c.value)).scalar_one() == "retained"
    finally:
        app.extensions["neofab2_db"].dispose()
