"""Managed lists, access control, atomic account validation and empty upgrade."""

import re
from html.parser import HTMLParser

import pytest
from alembic import command
from sqlalchemy import select, text

from neofab2 import create_app
from neofab2.core.users import create_user, edit_user, users
from neofab2.core.user_options import KINDS, options, save_option
from neofab2.database import upgrade_database, migration_config, database_ready


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    instance = create_app({"SECRET_KEY": "x" * 64, "DATA_DIR": str(tmp_path), "SESSION_COOKIE_SECURE": False, "TESTING": True})
    upgrade_database(instance)
    create_user(instance, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    yield instance
    instance.extensions["neofab2_db"].dispose()


def post(client, path, values, form=None):
    page = client.get(form or path)
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    return client.post(path, data={**values, "csrf_token": token})


def login(client, email="admin@example.org"):
    assert post(client, "/login", {"email": email, "password": "Test123!"}).status_code == 302


@pytest.mark.parametrize("kind", KINDS)
def test_separate_forms_persist_and_rename_assignments(app, kind):
    client = app.test_client()
    login(client)
    assert 'href="/admin/master-data"' in client.get("/admin/settings").text
    overview = client.get("/admin/master-data")
    assert overview.status_code == 200
    for list_kind in KINDS:
        assert f'href="/admin/user-options/{list_kind}"' in overview.text
    path = f"/admin/user-options/{kind}"
    assert "No options yet" in client.get(path).text
    assert 'href="/admin/master-data"' in client.get(path).text
    assert post(client, path, {"name": "Example", "active": "on"}).status_code == 302
    target = create_user(app, "person@example.org", "Person", "Test123!", actor_id=1, details={kind: "Example"})
    with app.extensions["neofab2_db"].connect() as connection:
        option_id = connection.execute(select(options.c.id)).scalar_one()
    assert post(client, f"{path}/{option_id}/edit", {"name": "Renamed", "active": "on"}).status_code == 302
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(users.c[kind]).where(users.c.id == target)).scalar_one() == "Renamed"
        assert connection.execute(select(options.c.name)).scalar_one() == "Renamed"
    page = client.get(f"/admin/users/{target}/edit")
    assert f'<select id="{kind}"' in page.text
    assert 'value="Renamed" selected' in page.text
    restarted = create_app(dict(app.config))
    try:
        with restarted.extensions["neofab2_db"].connect() as connection:
            assert connection.execute(select(options.c.name)).scalar_one() == "Renamed"
    finally:
        restarted.extensions["neofab2_db"].dispose()


def test_unknown_inactive_and_wrong_list_values_rejected_atomically(app):
    save_option(app, 1, "position", "Technician", True)
    target = create_user(app, "person@example.org", "Person", "Test123!", actor_id=1, details={"position": "Technician"})
    with app.extensions["neofab2_db"].connect() as connection:
        option_id = connection.execute(select(options.c.id)).scalar_one()
    save_option(app, 1, "position", "Technician", False, option_id)
    # Existing inactive assignment may be retained or cleared.
    edit_user(app, target, "person@example.org", "Person", "user", True, actor_id=1, details={"position": "Technician"})
    for data in [{"position": "Unknown"}, {"position": "Technician"}, {"cost_center": "Technician"}]:
        with pytest.raises(ValueError, match="active option"):
            create_user(app, "new@example.org", "New", "Test123!", actor_id=1, details=data)
    with pytest.raises(ValueError):
        edit_user(app, target, "changed@example.org", "Changed", "staff", True, actor_id=1, details={"position": "Forged"})
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(users.c.email, users.c.role).where(users.c.id == target)).one() == ("person@example.org", "user")
    edit_user(app, target, "person@example.org", "Person", "user", True, actor_id=1, details={"position": ""})
    with pytest.raises(ValueError):
        edit_user(app, target, "person@example.org", "Person", "user", True, actor_id=1, details={"position": "Technician"})


def test_catalog_validation_rights_csrf_and_escaping(app):
    client = app.test_client()
    login(client)
    path = "/admin/user-options/cost_center"
    assert client.post(path, data={"name": "Rejected", "active": "on"}).status_code == 400
    for name in ["", " " * 3, "x" * 101]:
        assert post(client, path, {"name": name, "active": "on"}).status_code == 400
    assert post(client, path, {"name": "Alpha", "active": "on"}).status_code == 302
    assert post(client, path, {"name": " Alpha ", "active": "on"}).status_code == 400
    assert post(client, path, {"name": "Bad", "active": "invalid"}).status_code == 400
    save_option(app, 1, "cost_center", "<script>example</script>", True)
    page = client.get(path).text
    assert "&lt;script&gt;example&lt;/script&gt;" in page and "<script>" not in page
    assert client.get("/admin/user-options/unknown").status_code == 404
    assert client.get("/admin/user-options/position/1/edit").status_code == 404
    for role in ["user", "staff"]:
        uid = create_user(app, f"{role}@example.org", role, "Test123!", role, actor_id=1)
        person = app.test_client()
        login(person, f"{role}@example.org")
        assert person.get(path).status_code == 403
        assert person.get("/admin/master-data").status_code == 403
        assert post(person, path, {"name": "Forbidden"}, form="/profile").status_code == 403
        with pytest.raises(PermissionError):
            save_option(app, uid, "position", "Forbidden", True)


def test_duplicate_rename_rolls_back_and_does_not_change_other_lists(app):
    save_option(app, 1, "position", "Alpha", True)
    save_option(app, 1, "position", "Beta", True)
    save_option(app, 1, "cost_center", "Alpha", True)
    uid = create_user(app, "person@example.org", "Person", "Test123!", actor_id=1, details={"position": "Alpha", "cost_center": "Alpha"})
    with app.extensions["neofab2_db"].connect() as connection:
        oid = connection.execute(select(options.c.id).where(options.c.kind == "position", options.c.name == "Alpha")).scalar_one()
    with pytest.raises(ValueError, match="already exists"):
        save_option(app, 1, "position", "Beta", False, oid)
    save_option(app, 1, "position", "Gamma", True, oid)
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(users.c.position, users.c.cost_center).where(users.c.id == uid)).one() == ("Gamma", "Alpha")


def test_schema_upgrade_creates_empty_lists_without_importing_legacy_text(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    instance = create_app({"SECRET_KEY": "x" * 64, "DATA_DIR": str(tmp_path)})
    try:
        config = migration_config()
        with instance.extensions["neofab2_db"].begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0006_english_default")
            connection.execute(text("INSERT INTO core_users (email, display_name, password_hash, role, active, created_at, position) VALUES ('old@example.org', 'Old', 'retained', 'admin', 1, 0, 'Legacy text')"))
        assert not database_ready(instance)
        upgrade_database(instance)
        upgrade_database(instance)
        assert database_ready(instance)
        with instance.extensions["neofab2_db"].connect() as connection:
            assert connection.execute(select(options)).all() == []
            assert connection.execute(select(users.c.position, users.c.password_hash)).one() == ("Legacy text", "retained")
            connection.execute(text("DROP TABLE core_user_options"))
            connection.commit()
        assert not database_ready(instance)
    finally:
        instance.extensions["neofab2_db"].dispose()


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.controls = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag in {"input", "select", "textarea"} and attrs.get("type") != "hidden":
            self.controls.append(attrs)


def test_help_is_associated_with_every_visible_field_and_can_be_translated(app, monkeypatch):
    from neofab2.core.i18n import MESSAGES
    client = app.test_client()
    pages = [client.get("/login")]
    login(client)
    pages += [client.get(path) for path in ["/profile", "/admin/users/new", "/admin/users/1/edit", "/admin/settings", "/admin/user-options/position"]]
    for page in pages:
        assert page.status_code == 200
        parsed = FormParser()
        parsed.feed(page.text)
        assert len(parsed.ids) == len(set(parsed.ids))
        for control in parsed.controls:
            assert control.get("aria-describedby") in parsed.ids, control
    message = "Select the person's organizational position, or leave this field empty."
    monkeypatch.setitem(MESSAGES, message, {"de": "Synthetic translated help"})
    post(client, "/profile", {"display_name": "Admin", "locale": "de"})
    assert "Synthetic translated help" in client.get("/admin/users/new").text
