"""N01: Aktivierung, Rechte, Abhängigkeiten und Aufgaben mit synthetischen Plugins."""

from dataclasses import replace
import re

from flask import Blueprint
import pytest
from click.testing import CliRunner

from neofab2 import create_app
from neofab2.cli import main
from neofab2.core.users import create_user
from neofab2.database import upgrade_database
from neofab2.plugin_api import Dependency, Plugin
from neofab2.plugin_api.registry import Registry
from neofab2.plugins.core_test import plugin


def synthetic(key, **kwargs):
    def factory():
        bp = Blueprint(f"plugin_{key}", __name__)
        bp.add_url_rule("/", "index", lambda: "synthetic", methods=["GET", "POST"])
        return bp
    return Plugin(key, key, "1.0.0", 1, f"{key}.access", ("admin",), factory, **kwargs)


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    return {"TESTING": True, "SECRET_KEY": "synthetic" * 8,
            "DATA_DIR": str(tmp_path / "data"), "SESSION_COOKIE_SECURE": False,
            "ENABLED_PLUGINS": ["core_test"]}


def login(client, email):
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    assert client.post("/login", data={"csrf_token": token, "email": email,
                                      "password": "Test123!"}).status_code == 302


def test_access_navigation_and_restart_deactivation(config):
    app = create_app(config)
    upgrade_database(app)
    admin = create_user(app, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    for role in ("user", "staff"):
        create_user(app, f"{role}@example.org", role, "Test123!", role, actor_id=admin)
    try:
        anonymous = app.test_client()
        assert anonymous.get("/plugins/core_test/").location == "/login"
        assert anonymous.get("/admin/plugins").location == "/login"
        for role in ("user", "staff"):
            client = app.test_client()
            login(client, f"{role}@example.org")
            assert client.get("/plugins/core_test/").status_code == 403
            assert client.get("/admin/plugins").status_code == 403
            assert "/plugins/core_test/" not in client.get("/profile").text
        client = app.test_client()
        login(client, "admin@example.org")
        assert client.get("/plugins/core_test/").status_code == 200
        assert "/plugins/core_test/" in client.get("/profile").text
        overview = client.get("/admin/plugins")
        assert overview.status_code == 200 and "0.1.0" in overview.text and "Aktiv" in overview.text
        registry = app.extensions["neofab2_plugins"]
        assert "erfolgreich" in registry.run_task("core_test", "self_check")
        cookie = client.get_cookie("neofab2_session").value
        restarted = create_app({**config, "ENABLED_PLUGINS": []})
        try:
            other = restarted.test_client()
            other.set_cookie("neofab2_session", cookie)
            assert other.get("/plugins/core_test/").status_code == 404
            assert "/plugins/core_test/" not in other.get("/profile").text
            assert "Deaktiviert" in other.get("/admin/plugins").text
            with pytest.raises(ValueError, match="nicht aktiv"):
                restarted.extensions["neofab2_plugins"].run_task("core_test", "self_check")
            # Deaktivierung erhält Konten, Schema und bestehende Core-Sitzung.
            assert other.get("/admin/users").status_code == 200
            assert other.get("/health/ready").status_code == 200
        finally:
            restarted.extensions["neofab2_db"].dispose()
    finally:
        app.extensions["neofab2_db"].dispose()


@pytest.mark.parametrize("plugins,enabled,message", [
    ([], ["missing"], "nicht installiert"),
    ([plugin, plugin], [], "Doppelte"),
    ([replace(plugin, api_version=2)], ["core_test"], "Inkompatible"),
    ([replace(plugin, permission="core.users.manage")], [], "Vertrag"),
    ([replace(plugin, version="bad")], [], "Version"),
    ([plugin], "core_test", "Liste"),
    ([plugin], ["core_test", "core_test"], "doppelte"),
    ([synthetic("a", dependencies=(Dependency("b", "1.0.0"),))], ["a"], "benötigt"),
    ([synthetic("a", dependencies=(Dependency("b", "2.0.0"),)), synthetic("b")], ["a", "b"], "ab 2.0.0"),
    ([synthetic("a", dependencies=(Dependency("b", "1.0.0"),)),
      synthetic("b", dependencies=(Dependency("a", "1.0.0"),))], ["a", "b"], "Zyklische"),
])
def test_invalid_registry_fails_closed(plugins, enabled, message):
    with pytest.raises(ValueError, match=message):
        Registry(plugins, enabled)


def test_dependency_order_and_no_admin_wildcard():
    a = synthetic("a", dependencies=(Dependency("b", "1.0.0"),))
    b = replace(synthetic("b"), roles=("staff",))
    registry = Registry((a, b), ["a", "b"])
    assert [item.plugin_id for item in registry.ordered] == ["b", "a"]
    assert not registry.allows({"active": True, "role": "admin"}, "b.access")
    assert registry.allows({"active": True, "role": "staff"}, "b.access")
    assert not registry.allows({"active": False, "role": "staff"}, "b.access")
    with pytest.raises(ValueError, match="benötigt"):
        Registry((a, b), ["a"])


def test_plugin_post_keeps_csrf_protection(config):
    app = create_app({**config, "ENABLED_PLUGINS": ["a"]}, plugins=(synthetic("a"),))
    try:
        upgrade_database(app)
        create_user(app, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
        client = app.test_client()
        login(client, "admin@example.org")
        assert client.post("/plugins/a/").status_code == 400
        with client.session_transaction() as session:
            session_token = session.get("auth_token")
        assert session_token
        page = client.get("/profile")
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        assert client.post("/plugins/a/", data={"csrf_token": csrf}).status_code == 200
    finally:
        app.extensions["neofab2_db"].dispose()


def test_cli_task_respects_config_activation(config, tmp_path, monkeypatch):
    import json
    filename = tmp_path / "config.toml"
    content = f'SECRET_KEY = "{"s" * 64}"\nDATA_DIR = {json.dumps(config["DATA_DIR"])}\n'
    filename.write_text(content + 'ENABLED_PLUGINS = ["core_test"]\n', encoding="utf-8")
    monkeypatch.setenv("NEOFAB2_CONFIG", str(filename))
    runner = CliRunner()
    assert runner.invoke(main, ["migrate"]).exit_code == 0
    result = runner.invoke(main, ["plugin-task", "core_test", "self_check"])
    assert result.exit_code == 0 and "erfolgreich" in result.output
    assert runner.invoke(main, ["plugin-task", "core_test", "missing"]).exit_code == 1
    filename.write_text(content, encoding="utf-8")
    result = runner.invoke(main, ["plugin-task", "core_test", "self_check"])
    assert result.exit_code == 1 and "nicht aktiv" in result.output
