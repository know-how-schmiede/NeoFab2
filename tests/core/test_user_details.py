"""U05: Screenshot-Felder, optionale Passwortänderung und private Admin-Daten."""

import re
from alembic import command
import pytest
from sqlalchemy import select, text
from werkzeug.security import check_password_hash

from neofab2 import create_app
from neofab2.database import upgrade_database, database_ready, migration_config
from neofab2.core.users import create_user, users, sessions, DETAIL_FIELDS, edit_user


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    instance = create_app({"SECRET_KEY": "x" * 64, "DATA_DIR": str(tmp_path), "SESSION_COOKIE_SECURE": False, "TESTING": True})
    upgrade_database(instance)
    create_user(instance, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    yield instance
    instance.extensions["neofab2_db"].dispose()


def post(client, path, data, form=None):
    page = client.get(form or path)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    return client.post(path, data={**data, "csrf_token": token})


def login(client, email="admin@example.org", password="Test123!"):
    return post(client, "/login", {"email": email, "password": password})


def record(app, email):
    with app.extensions["neofab2_db"].connect() as connection:
        return connection.execute(select(users).where(users.c.email == email)).mappings().one()


def test_both_forms_round_trip_all_fields_and_clear(app):
    client = app.test_client()
    assert login(client).status_code == 302
    details = {key: "Synthetic " + key for key in DETAIL_FIELDS}
    from neofab2.core.user_options import KINDS, save_option
    for kind in KINDS:
        save_option(app, 1, kind, details[kind], True)
    data = {**details, "email": "test@example.org", "display_name": "Test", "role": "user",
            "locale": "fr", "active": "off", "password": "Test123!", "confirm_password": "Test123!"}
    page = client.get("/admin/users/new")
    assert all(f'name="{key}"' in page.text for key in DETAIL_FIELDS)
    assert post(client, "/admin/users/new", data).status_code == 302
    row = record(app, "test@example.org")
    assert not row["active"] and row["locale"] == "fr"
    assert all(row[key] == value for key, value in details.items())
    assert login(app.test_client(), "test@example.org").status_code == 401
    path = f'/admin/users/{row["id"]}/edit'
    assert all(value in client.get(path).text for value in details.values())
    data.update({"active": "on", "locale": "en", "note": "", "confirm_password": ""})
    assert post(client, path, data).status_code == 302
    row = record(app, "test@example.org")
    assert row["active"] and row["locale"] == "en" and row["note"] == ""
    assert check_password_hash(row["password_hash"], "Test123!")
    ordinary = app.test_client()
    assert login(ordinary, "test@example.org").status_code == 302
    assert ordinary.get(path).status_code == 403
    assert "Synthetic address" not in ordinary.get("/profile").text


def test_optional_admin_password_is_atomic_and_revokes_sessions(app):
    target = create_user(app, "test@example.org", "Test", "Test123!", actor_id=1)
    client = app.test_client()
    login(client)
    person = app.test_client()
    login(person, "test@example.org")
    path = f"/admin/users/{target}/edit"
    data = {"email": "test@example.org", "display_name": "Changed", "role": "user", "active": "on",
            "new_password": "Reset12!", "confirm_password": "Mismatch!", "note": "Must not persist"}
    response = post(client, path, data)
    assert response.status_code == 400 and "Reset12!" not in response.text
    assert record(app, "test@example.org")["display_name"] == "Test"
    assert person.get("/profile").status_code == 200
    data["confirm_password"] = "Reset12!"
    assert post(client, path, data).status_code == 302
    assert person.get("/profile").status_code == 302
    assert login(app.test_client(), "test@example.org", "Reset12!").status_code == 302
    assert login(app.test_client(), "test@example.org", "Test123!").status_code == 401


@pytest.mark.parametrize("field", list(DETAIL_FIELDS))
def test_field_limits_reject_without_partial_write(app, field):
    limit = DETAIL_FIELDS[field][1]
    with pytest.raises(ValueError):
        create_user(app, "long@example.org", "Test", "Test123!", actor_id=1, details={field: "x" * (limit + 1)})
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(users.c.id).where(users.c.email == "long@example.org")).first() is None


def test_admin_fields_escape_html_and_self_profile_cannot_modify_them(app):
    target = create_user(app, "test@example.org", "Test", "Test123!", actor_id=1, details={"note": "<script>private</script>"})
    admin = app.test_client()
    login(admin)
    page = admin.get(f"/admin/users/{target}/edit")
    assert "&lt;script&gt;private&lt;/script&gt;" in page.text and "<script>" not in page.text
    person = app.test_client()
    login(person, "test@example.org")
    assert post(person, "/profile", {"display_name": "Updated", "note": "injected", "cost_center": "injected"}).status_code == 302
    row = record(app, "test@example.org")
    assert row["note"] == "<script>private</script>" and row["cost_center"] == ""
    with pytest.raises(ValueError, match="last active"):
        edit_user(app, 1, "admin@example.org", "Admin", "user", True, actor_id=1, new_password="Changed!")
    assert check_password_hash(record(app, "admin@example.org")["password_hash"], "Test123!")


def test_explicit_migration_retains_existing_values(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "x" * 64, "DATA_DIR": str(tmp_path)})
    try:
        cfg = migration_config()
        with app.extensions["neofab2_db"].begin() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "0004_user_locale")
            connection.execute(text("INSERT INTO core_users (email, display_name, password_hash, role, active, created_at, theme, locale) VALUES ('old@example.org','Old','hash-retained','admin',1,0,'light','fr')"))
        assert not database_ready(app)
        upgrade_database(app)
        upgrade_database(app)
        row = record(app, "old@example.org")
        assert all(row[key] == "" for key in DETAIL_FIELDS)
        assert row["locale"] == "fr" and row["theme"] == "light" and row["password_hash"] == "hash-retained"
    finally:
        app.extensions["neofab2_db"].dispose()
