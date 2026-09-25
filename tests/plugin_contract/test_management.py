"""N01/U06: Backend-Auswahl, Neustart, Abhängigkeiten und Wiederherstellung."""

from concurrent.futures import ThreadPoolExecutor
import json
import re

from click.testing import CliRunner
import pytest
from sqlalchemy import select, update

from neofab2 import create_app
from neofab2.cli import main
from neofab2.core.plugin_state import STATE_KEY, change_selection, read_selection
from neofab2.core.settings import settings
from neofab2.core.users import create_user, users
from neofab2.database import upgrade_database
from neofab2.plugin_api import Plugin
from flask import Blueprint


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    return {"TESTING": True, "SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path / "data"),
            "SESSION_COOKIE_SECURE": False, "ENABLED_PLUGINS": []}


@pytest.fixture
def app(config):
    app = create_app(config)
    upgrade_database(app)
    admin = create_user(app, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    for role in ("user", "staff"):
        create_user(app, f"{role}@example.org", role, "Test123!", role, actor_id=admin)
    yield app
    app.extensions["neofab2_db"].dispose()


def token(client, path):
    page = client.get(path)
    return re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)


def login(client, role="admin"):
    assert client.post("/login", data={"email": f"{role}@example.org", "password": "Test123!",
                                       "csrf_token": token(client, "/login")}).status_code == 302


def change(client, plugin_id, action, form="/admin/plugins"):
    return client.post(f"/admin/plugins/{plugin_id}/state",
                       data={"action": action, "csrf_token": token(client, form)})


def test_backend_selection_applies_on_restart_and_config_is_fallback(app, config):
    client = app.test_client()
    login(client)
    assert read_selection(app) == ([], "config")
    assert change(client, "core_test", "enable").status_code == 302
    assert change(client, "management_test", "enable").status_code == 302
    assert read_selection(app) == (["core_test", "management_test"], "database")
    assert app.config["ENABLED_PLUGINS"] == []
    assert "Restart required" in client.get("/admin/plugins").text
    assert client.get("/plugins/management_test/").status_code == 404
    assert "/plugins/management_test/" not in client.get("/profile").text
    restarted = create_app(config)
    try:
        new_client = restarted.test_client()
        new_client.set_cookie("neofab2_session", client.get_cookie("neofab2_session").value)
        assert "Restart required" not in new_client.get("/admin/plugins").text
        assert new_client.get("/plugins/management_test/").status_code == 200
        assert "/plugins/management_test/" in new_client.get("/profile").text
        assert new_client.post("/plugins/management_test/check").status_code == 400
        result = new_client.post("/plugins/management_test/check", data={
            "csrf_token": token(new_client, "/plugins/management_test/")}, follow_redirects=True)
        assert "Management test successful" in result.text
        assert "successfully" in restarted.extensions["neofab2_plugins"].run_task("management_test", "self_check")
        assert change(new_client, "management_test", "disable").status_code == 302
        assert change(new_client, "core_test", "disable").status_code == 302
        # Registrierung bleibt geladen; Dateidienst sperrt ab 0.1.17 sofort.
        assert new_client.get("/plugins/management_test/").status_code == 404
        assert "Restart required" in new_client.get("/admin/plugins").text
        disabled = create_app({**config, "ENABLED_PLUGINS": ["core_test"]})
        try:
            assert disabled.extensions["neofab2_plugins"].enabled == frozenset()
            assert disabled.test_client().get("/plugins/management_test/").status_code == 404
            with pytest.raises(ValueError, match="not active"):
                disabled.extensions["neofab2_plugins"].run_task("management_test", "self_check")
        finally:
            disabled.extensions["neofab2_db"].dispose()
    finally:
        restarted.extensions["neofab2_db"].dispose()


def test_dependency_failures_do_not_change_saved_state(app):
    client = app.test_client()
    login(client)
    result = change(client, "management_test", "enable")
    assert result.status_code == 400 and "requires" in result.text
    assert read_selection(app) == ([], "config")
    assert change(client, "core_test", "enable").status_code == 302
    assert change(client, "management_test", "enable").status_code == 302
    before = read_selection(app)
    result = change(client, "core_test", "disable")
    assert result.status_code == 400 and "requires" in result.text
    assert read_selection(app) == before


def test_selection_rights_csrf_and_method(app):
    assert app.test_client().post("/admin/plugins/core_test/state").status_code == 400
    for role in ("user", "staff"):
        client = app.test_client()
        login(client, role)
        assert change(client, "core_test", "enable", form="/profile").status_code == 403
    client = app.test_client()
    login(client)
    assert client.get("/admin/plugins/core_test/state").status_code == 405
    assert client.post("/admin/plugins/core_test/state", data={"action": "enable"}).status_code == 400
    assert read_selection(app) == ([], "config")


@pytest.mark.parametrize("plugin_id,action", [("unknown", "enable"), ("core_test", "restart"), ("core_test", "")])
def test_invalid_change_rejected(app, plugin_id, action):
    client = app.test_client()
    login(client)
    assert change(client, plugin_id, action).status_code == 400
    assert read_selection(app) == ([], "config")


def test_reverted_pending_change_needs_no_restart(app):
    client = app.test_client()
    login(client)
    assert change(client, "core_test", "enable").status_code == 302
    assert change(client, "core_test", "disable").status_code == 302
    assert "Restart required" not in client.get("/admin/plugins").text
    assert read_selection(app) == ([], "database")


def test_revoked_admin_cannot_save(app):
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(update(users).where(users.c.id == 1).values(active=False))
    with pytest.raises(PermissionError):
        change_selection(app, 1, "core_test", "enable")
    assert read_selection(app) == ([], "config")


def test_concurrent_changes_keep_both_choices(config):
    def synthetic(key):
        def factory():
            bp = Blueprint(f"plugin_{key}", __name__)
            bp.add_url_rule("/", "index", lambda: "test")
            return bp
        return Plugin(key, key, "0.1.0", 1, f"{key}.access", ("admin",), factory)
    app = create_app(config, plugins=(synthetic("a"), synthetic("b")))
    try:
        upgrade_database(app)
        admin = create_user(app, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda key: change_selection(app, admin, key, "enable"), ("a", "b")))
        assert read_selection(app) == (["a", "b"], "database")
    finally:
        app.extensions["neofab2_db"].dispose()


def test_existing_config_selection_and_no_factory_writes(config):
    config = {**config, "ENABLED_PLUGINS": ["core_test"]}
    app = create_app(config)
    try:
        upgrade_database(app)
        assert app.extensions["neofab2_plugins"].enabled == {"core_test"}
        with app.extensions["neofab2_db"].connect() as connection:
            assert connection.execute(select(settings.c.value).where(settings.c.key == STATE_KEY)).first() is None
    finally:
        app.extensions["neofab2_db"].dispose()


def test_corrupt_state_fails_closed_and_cli_recovery(app, config, tmp_path, monkeypatch):
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(settings.insert().values(key=STATE_KEY, value="not-json"))
        connection.execute(settings.insert().values(key="unrelated", value="retained"))
    with pytest.raises(ValueError, match="plugin selection"):
        create_app(config)
    filename = tmp_path / "config.toml"
    filename.write_text(f'SECRET_KEY = "{"s" * 64}"\nDATA_DIR = {json.dumps(config["DATA_DIR"])}\nENABLED_PLUGINS = ["core_test"]\n', encoding="utf-8")
    monkeypatch.setenv("NEOFAB2_CONFIG", str(filename))
    runner = CliRunner()
    assert runner.invoke(main, ["plugins-restore-config"], input="n\n").exit_code == 1
    result = runner.invoke(main, ["plugins-restore-config"], input="y\n")
    assert result.exit_code == 0, result.output
    assert "Restart" in result.output
    recovered = create_app()
    try:
        assert recovered.extensions["neofab2_plugins"].enabled == {"core_test"}
        with recovered.extensions["neofab2_db"].connect() as connection:
            assert connection.execute(select(settings.c.value).where(settings.c.key == "unrelated")).scalar_one() == "retained"
    finally:
        recovered.extensions["neofab2_db"].dispose()
