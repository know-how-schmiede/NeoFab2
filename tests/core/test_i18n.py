"""S02/U07: Gast-/Kontosprache, Fallback, CSRF und Schema-Upgrade."""

import re

from alembic import command
import pytest
from sqlalchemy import select, text

from neofab2 import create_app
from neofab2.core.i18n import translate
from neofab2.core.users import create_user, users
from neofab2.database import database_ready, migration_config, upgrade_database


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path), "SESSION_COOKIE_SECURE": False, "TESTING": True})
    upgrade_database(app)
    create_user(app, "admin@example.org", "Test", "Test123!", "admin", bootstrap=True)
    yield app
    app.extensions["neofab2_db"].dispose()


def post(client, path, data, form="/login", **kwargs):
    page = client.get(form)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    return client.post(path, data={**data, "csrf_token": token}, **kwargs)


@pytest.mark.parametrize("locale,label", [("de", "Anmelden"), ("en", "Sign in"), ("fr", "Se connecter")])
def test_guest_language_and_login_error(app, locale, label):
    client = app.test_client()
    assert post(client, "/language", {"locale": locale}).status_code == 302
    page = client.get("/login")
    assert f'lang="{locale}"' in page.text and f"<h1>{label}</h1>" in page.text
    error = post(client, "/login", {"email": "unknown@example.org", "password": "Wrong123!"})
    assert error.status_code == 401
    assert {"de": "Zugangsdaten", "en": "credentials", "fr": "identifiants"}[locale] in error.text


def test_account_language_persists_and_overrides_guest_choice(app):
    client = app.test_client()
    assert post(client, "/login", {"email": "admin@example.org", "password": "Test123!"}).status_code == 302
    assert post(client, "/profile", {"display_name": "French account", "locale": "fr"}, form="/profile").status_code == 302
    page = client.get("/profile")
    assert '<h1>Mon profil</h1>' in page.text and 'lang="fr"' in page.text
    assert "Profil enregistré." in page.text
    assert post(client, "/logout", {}, form="/profile").status_code == 302
    assert 'lang="fr"' in client.get("/login").text
    assert post(client, "/language", {"locale": "en"}).status_code == 302
    assert post(client, "/login", {"email": "admin@example.org", "password": "Test123!"}).status_code == 302
    assert 'lang="fr"' in client.get("/profile").text


def test_invalid_language_and_csrf_do_not_change_account(app):
    client = app.test_client()
    assert client.post("/language", data={"locale": "fr"}).status_code == 400
    assert post(client, "/language", {"locale": "unknown"}).status_code == 400
    assert post(client, "/login", {"email": "admin@example.org", "password": "Test123!"}).status_code == 302
    assert post(client, "/profile", {"display_name": "Changed", "locale": "xx"}, form="/profile").status_code == 400
    with app.extensions["neofab2_db"].connect() as connection:
        row = connection.execute(select(users.c.locale, users.c.display_name)).one()
        assert row == ("de", "Test")


def test_unknown_translation_falls_back_and_is_escaped(app):
    from flask import g, render_template_string, session
    with app.test_request_context():
        g.current_user = None
        session["locale"] = "fr"
        assert translate("Noch nicht übersetzt") == "Noch nicht übersetzt"
        assert render_template_string("{{ _(message) }}", message="<script>test</script>") == "&lt;script&gt;test&lt;/script&gt;"
        session["locale"] = "unsupported"
        assert translate("Anmelden") == "Anmelden"


def test_upgrade_015_preserves_existing_user_and_defaults_to_german(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path)})
    try:
        config = migration_config()
        with app.extensions["neofab2_db"].begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0003_user_theme")
            connection.execute(text("INSERT INTO core_users (email, display_name, password_hash, role, active, created_at, theme) VALUES ('test@example.org', 'Synthetic', 'retained-hash', 'admin', 1, 0, 'light')"))
        assert not database_ready(app)
        upgrade_database(app)
        upgrade_database(app)
        assert database_ready(app)
        with app.extensions["neofab2_db"].connect() as connection:
            row = connection.execute(select(users.c.locale, users.c.theme, users.c.password_hash)).one()
            assert row == ("de", "light", "retained-hash")
    finally:
        app.extensions["neofab2_db"].dispose()
