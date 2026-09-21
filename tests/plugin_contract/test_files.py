"""N01/U06/S10: multi-permission and owner-scoped file contract; synthetic data."""

from dataclasses import replace
from io import BytesIO
import re
import sqlite3

from alembic import command
import pytest
from sqlalchemy import select, update

from neofab2 import create_app
from neofab2.core.users import create_user, users
from neofab2.database import database_ready, migration_config, upgrade_database
from neofab2.plugin_api import Permission, owns_or_allowed
from neofab2.plugin_api.files import download_file
from neofab2.plugin_api.registry import Registry
from neofab2.plugins.core_test import plugin as core
from neofab2.plugins.management_test import plugin
from neofab2.services.files import files

ROOT = "/plugins/management_test/"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    instance = create_app({"SECRET_KEY": "synthetic" * 8, "DATA_DIR": str(tmp_path),
        "TESTING": True, "SESSION_COOKIE_SECURE": False,
        "ENABLED_PLUGINS": ["core_test", "management_test"]})
    upgrade_database(instance)
    create_user(instance, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    for name, role in [("one", "user"), ("two", "user"), ("staff", "staff")]:
        create_user(instance, f"{name}@example.org", name, "Test123!", role, actor_id=1)
    yield instance
    instance.extensions["neofab2_db"].dispose()


def token(client, path=ROOT):
    return re.search(r'name="csrf_token" value="([^"]+)"', client.get(path).text).group(1)


def login(app, name):
    client = app.test_client()
    assert client.post("/login", data={"email": f"{name}@example.org", "password": "Test123!",
        "csrf_token": token(client, "/login")}).status_code == 302
    return client


def upload(client, content=b"synthetic", filename="test.txt", **extra):
    return client.post(ROOT + "files", data={"csrf_token": token(client),
        "file": (BytesIO(content), filename), **extra})


def file_id(app):
    with app.extensions["neofab2_db"].connect() as connection:
        return connection.execute(select(files.c.id)).scalar_one()


def test_owner_staff_and_admin_direct_access_and_csrf(app):
    one, two, staff, admin = [login(app, name) for name in ("one", "two", "staff", "admin")]
    assert upload(one, owner_id="3", plugin_id="core_test").status_code == 302
    key = file_id(app)
    path = ROOT + "files/" + key
    response = one.get(path)
    assert response.data == b"synthetic" and response.status_code == 200
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert response.mimetype == "application/octet-stream"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"
    assert key not in two.get(ROOT).text
    assert two.get(path).status_code == 404
    assert app.test_client().get(path).location == "/login"
    for client in (staff, admin):
        assert key in client.get(ROOT).text and client.get(path).data == b"synthetic"
        assert client.post(ROOT + "check", data={"csrf_token": token(client)}).status_code == 302
    assert one.post(ROOT + "check", data={"csrf_token": token(one)}).status_code == 403
    assert "Test form access" not in one.get(ROOT).text
    assert one.post(ROOT + "files", data={"file": (BytesIO(b"x"), "x.txt")}).status_code == 400
    with app.extensions["neofab2_db"].connect() as connection:
        row = connection.execute(select(files)).mappings().one()
        assert row["owner_id"] == 2 and row["plugin_id"] == "management_test"


@pytest.mark.parametrize("name,content,status", [
    ("../secret.txt", b"x", 400), ("..\\secret.txt", b"x", 400),
    ("C:secret.txt", b"x", 400), ("test.html", b"<script>x</script>", 400),
    ("empty.txt", b"", 400), ("big.txt", b"x" * 262145, 413),
    ("request.txt", b"x" * 1048577, 413), ("x" * 201 + ".txt", b"x", 400),
], ids=["parent-posix", "parent-windows", "drive", "html", "empty", "file-limit", "request-limit", "long-name"])
def test_invalid_uploads_leave_no_record(app, name, content, status):
    assert upload(login(app, "one"), content, name).status_code == status
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(files.c.id)).first() is None


def test_size_boundary_restart_deactivation_and_backup(app, tmp_path):
    client = login(app, "one")
    assert upload(client, b"x" * 262144).status_code == 302
    key = file_id(app)
    restarted = create_app(dict(app.config))
    try:
        assert login(restarted, "one").get(ROOT + "files/" + key).data == b"x" * 262144
    finally:
        restarted.extensions["neofab2_db"].dispose()
    disabled = create_app({**app.config, "ENABLED_PLUGINS": []})
    try:
        other = login(disabled, "one")
        assert other.get(ROOT).status_code == 404
        assert other.get(ROOT + "files/" + key).status_code == 404
        assert ROOT not in other.get("/profile").text
        with pytest.raises(ValueError, match="not active"):
            disabled.extensions["neofab2_plugins"].run_task("management_test", "self_check")
        with disabled.test_request_context():
            from werkzeug.exceptions import NotFound
            with pytest.raises(NotFound):
                download_file("management_test", key)
    finally:
        disabled.extensions["neofab2_db"].dispose()
    backup = tmp_path / "synthetic-backup.sqlite3"
    with sqlite3.connect(tmp_path / "neofab2.sqlite3") as source, sqlite3.connect(backup) as destination:
        source.backup(destination)
        assert destination.execute("SELECT content FROM core_files WHERE id=?", (key,)).fetchone()[0] == b"x" * 262144
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(files.c.id)).scalar_one() == key


def test_namespace_and_revoked_account(app):
    client = login(app, "one")
    assert upload(client).status_code == 302
    key = file_id(app)
    # Wrong module: identical policy cannot expose another module's file.
    foreign = replace(core, files=plugin.files, permissions=plugin.permissions)
    with pytest.raises(ValueError, match="permission contract"):
        Registry([foreign], ["core_test"])
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(update(files).where(files.c.id == key).values(plugin_id="other"))
    assert client.get(ROOT + "files/" + key).status_code == 404
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(update(users).where(users.c.id == 2).values(active=False))
    assert client.get(ROOT).location == "/login"


@pytest.mark.parametrize("permissions", [
    (Permission("core.users.manage", ("admin",)),),
    (Permission("management_test.access", ("admin",)),),
    (Permission("management_test.upload", ("employee",)),),
    (Permission("management_test.upload", ()),),
    (Permission("management_test.x", ("admin",)), Permission("management_test.x", ("user",))),
])
def test_permission_contract_validation(permissions):
    with pytest.raises(ValueError, match="permission contract"):
        Registry([replace(plugin, permissions=permissions)], [])


def test_ownership_requires_explicit_permission_and_no_admin_wildcard(app):
    with app.app_context():
        user = {"id": 2, "active": True, "role": "user"}
        assert owns_or_allowed(user, 2, "management_test.read_own", "management_test.read_all")
        assert not owns_or_allowed(user, 3, "management_test.read_own", "management_test.read_all")
        assert not owns_or_allowed(user, 2, "management_test.missing", "management_test.missing")
        assert not owns_or_allowed({**user, "active": False}, 2, "management_test.read_own", "management_test.read_all")
    registry = Registry([core, replace(plugin, permissions=(Permission("management_test.staff_only", ("staff",)),), files=None)], ["core_test", "management_test"])
    assert not registry.allows({"active": True, "role": "admin"}, "management_test.staff_only")
    assert registry.allows({"active": True, "role": "staff"}, "management_test.staff_only")


@pytest.mark.parametrize("changes", [
    {"upload": "core.users.manage"}, {"read_all": "management_test.read_own"},
    {"max_bytes": 0}, {"max_bytes": 1048577}, {"max_bytes": True},
    {"extensions": ()}, {"extensions": ("../txt",)},
])
def test_file_policy_fails_closed(changes):
    with pytest.raises(ValueError, match="file contract"):
        Registry([replace(plugin, files=replace(plugin.files, **changes))], [])


def test_upload_checks_specific_permission_and_current_account(app):
    client = login(app, "one")
    restricted = replace(plugin, permissions=tuple(
        replace(p, roles=("staff",)) if p.name == "management_test.upload" else p
        for p in plugin.permissions))
    app.extensions["neofab2_plugins"] = Registry([core, restricted], ["core_test", "management_test"])
    assert upload(client).status_code == 403
    assert upload(login(app, "admin")).status_code == 403
    assert upload(login(app, "staff")).status_code == 302
    with app.test_request_context():
        from flask import g
        from werkzeug.datastructures import FileStorage
        from neofab2.plugin_api.files import store_file
        g.current_user = {"id": 4, "active": True, "role": "staff"}
        with app.extensions["neofab2_db"].begin() as connection:
            connection.execute(update(users).where(users.c.id == 4).values(active=False))
        with pytest.raises(PermissionError):
            store_file("management_test", FileStorage(stream=BytesIO(b"x"), filename="test.txt"))


def test_explicit_upgrade_from_019_preserves_accounts(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path)})
    try:
        config = migration_config()
        with app.extensions["neofab2_db"].begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "0007_user_options")
        # Seed the historical schema directly; current user creation requires audit schema.
        from werkzeug.security import generate_password_hash
        with app.extensions["neofab2_db"].begin() as connection:
            connection.execute(users.insert().values(email="admin@example.org", display_name="Existing",
                password_hash=generate_password_hash("Test123!"), role="admin", active=True, created_at=1))
        # Compare the columns that existed in 0007; later revisions add metadata.
        original_columns = [column for column in users.c if column.name != "activation_pending"]
        with app.extensions["neofab2_db"].connect() as connection:
            before = connection.execute(select(*original_columns)).all()
        assert not database_ready(app)
        upgrade_database(app)
        upgrade_database(app)
        assert database_ready(app)
        with app.extensions["neofab2_db"].connect() as connection:
            assert connection.execute(select(*original_columns)).all() == before
            assert connection.execute(select(users.c.activation_pending)).scalar_one() is False
            assert connection.execute(select(files)).first() is None
    finally:
        app.extensions["neofab2_db"].dispose()


def test_administration_navigation_and_direct_permissions(app):
    assert app.test_client().get("/admin").location == "/login"
    for name in ("one", "staff"):
        client = login(app, name)
        assert 'href="/admin"' not in client.get("/profile").text
        for path in ("/admin", "/admin/users", "/admin/plugins", "/admin/settings"):
            assert client.get(path).status_code == 403
    admin = login(app, "admin")
    page = admin.get("/profile").text
    assert 'href="/admin"' in page
    for path in ("/admin/users", "/admin/plugins", "/admin/settings"):
        assert f'href="{path}"' not in page
        assert f'href="{path}"' in admin.get("/admin").text
