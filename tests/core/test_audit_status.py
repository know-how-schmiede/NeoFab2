"""S09/S12/N01: synthetic audit, retention, state and migration contracts."""
from dataclasses import replace
import re
import sqlite3
from pathlib import Path

import pytest
from alembic import command
from click.testing import CliRunner
from flask import g
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from neofab2 import create_app
from neofab2.core import auth
from neofab2.core.users import create_user, edit_user, change_password, reset_admin_password, users, write_transaction
from neofab2.core.plugin_state import change_selection
from neofab2.database import database_ready, migration_config, upgrade_database
from neofab2.services import audit, mail, operations
from neofab2.plugin_api import Permission
from neofab2.plugin_api.audit import record_action
from neofab2.plugins.core_test import plugin

TEST_PLUGIN = replace(plugin, roles=("staff", "admin"), permissions=(*plugin.permissions, Permission("core_test.action", ("staff",)),))
PASSWORD = "Synthetic123!"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"TESTING": True, "SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path),
                      "SESSION_COOKIE_SECURE": False, "SMTP_PASSWORD": "synthetic-smtp-secret",
                      "ENABLED_PLUGINS": ["core_test"]}, plugins=[TEST_PLUGIN])
    upgrade_database(app)
    create_user(app, "admin@example.org", "Admin", PASSWORD, "admin", bootstrap=True)
    create_user(app, "staff@example.org", "Staff", PASSWORD, "staff", actor_id=1)
    create_user(app, "user@example.org", "User", PASSWORD, actor_id=1)
    yield app
    app.extensions["neofab2_db"].dispose()


def rows(app):
    with app.extensions["neofab2_db"].connect() as conn:
        return [dict(row) for row in conn.execute(select(audit.events)).mappings()]


def login(app, role="admin"):
    client = app.test_client()
    token = re.search(r'name="csrf_token" value="([^"]+)"', client.get("/login").text).group(1)
    assert client.post("/login", data={"email": f"{role}@example.org", "password": PASSWORD, "csrf_token": token}).status_code == 302
    return client


@pytest.mark.parametrize("path", ["/admin/audit", "/admin/status"])
def test_admin_only_and_read_only(app, path):
    assert app.test_client().get(path).location == "/login"
    for role in ("user", "staff"):
        assert login(app, role).get(path).status_code == 403
    client = login(app)
    before = rows(app)
    page = client.get(path)
    assert page.status_code == 200
    assert rows(app) == before
    assert client.post(path).status_code in (400, 405)
    assert app.config["SMTP_PASSWORD"] not in page.text
    assert app.config["SECRET_KEY"] not in page.text


def test_audit_records_no_secrets_or_untrusted_text(app):
    assert auth.authenticate(app, "unknown@example.org", "never-record-this", "192.0.2.4") is None
    token = auth.authenticate(app, "admin@example.org", PASSWORD, "192.0.2.4")
    assert token
    edit_user(app, 3, "changed@example.org", "<script>secret-note</script>", "staff", True, actor_id=1,
              new_password="Changed123!")
    change_password(app, 3, "Changed123!", "Changed456!")
    reset_admin_password(app, 1, "Emergency123!")
    data = repr(rows(app))
    for forbidden in (token, PASSWORD, "never-record-this", "192.0.2.4", "changed@example.org", "script", "Emergency123!", "Changed123!", "scrypt"):
        assert forbidden not in data
    names = {r["event"] for r in rows(app)}
    assert {"user.created", "user.updated", "login.failed", "login.succeeded", "password.changed", "password.emergency_reset"} <= names
    for value in ("<script>", "smtp-password", "login.failed\nsecret"):
        with pytest.raises(ValueError), write_transaction(app) as conn:
            audit.record(conn, value)
    with pytest.raises(ValueError), write_transaction(app) as conn:
        audit.record(conn, "user.updated", target_id="secret")


def test_transaction_rollback_and_fail_closed_audit(app):
    before = rows(app)
    with pytest.raises(RuntimeError), write_transaction(app) as conn:
        audit.record(conn, "user.updated", actor_id=1, target_id=3)
        raise RuntimeError("rollback")
    assert rows(app) == before
    with app.extensions["neofab2_db"].begin() as conn:
        conn.exec_driver_sql("DROP TABLE core_audit_events")
    with pytest.raises(SQLAlchemyError):
        edit_user(app, 3, "new@example.org", "Changed", "user", True, actor_id=1)
    with app.extensions["neofab2_db"].connect() as conn:
        assert conn.execute(select(users.c.email).where(users.c.id == 3)).scalar_one() == "user@example.org"
    assert not database_ready(app)


def test_filters_pagination_and_german_labels(app):
    with write_transaction(app) as conn:
        conn.execute(update(users).where(users.c.id == 1).values(locale="de"))
        for _ in range(55):
            audit.record(conn, "login.failed")
    client = login(app)
    assert "Audit-Protokoll" in client.get("/admin").text
    page = client.get("/admin/audit?event=login.failed").text
    assert "Nächste Seite" in page and "Anmeldung fehlgeschlagen" in page
    assert "Vorherige Seite" in client.get("/admin/audit?event=login.failed&page=2").text
    assert client.get("/admin/audit?event=secret").status_code == 400
    assert "Betriebsstatus" in client.get("/admin/status").text


def test_retention_boundary_preview_and_confirmation(app, monkeypatch):
    from neofab2.cli import main
    monkeypatch.setattr("neofab2.cli.ready_app", lambda: app)
    now = 2_000_000_000
    monkeypatch.setattr(audit.time, "time", lambda: now)
    with write_transaction(app) as conn:
        conn.execute(update(audit.events).values(created_at=now))
        key = audit.record(conn, "login.failed")
        conn.execute(update(audit.events).where(audit.events.c.id == key).values(created_at=now - 180*86400 - 1))
        key = audit.record(conn, "login.failed")
        conn.execute(update(audit.events).where(audit.events.c.id == key).values(created_at=now - 180*86400))
    runner = CliRunner()
    before = rows(app)
    preview = runner.invoke(main, ["audit-prune"])
    assert preview.exit_code == 0 and "Preview only" in preview.output
    assert rows(app) == before
    assert runner.invoke(main, ["audit-prune", "--apply"], input="n\n").exit_code != 0
    assert rows(app) == before
    result = runner.invoke(main, ["audit-prune", "--apply"], input="y\n")
    assert result.exit_code == 0 and "deleted: 1" in result.output
    assert rows(app)[-1]["event"] == "audit.pruned" and rows(app)[-1]["count"] == 1
    assert len(rows(app)) == len(before)
    assert runner.invoke(main, ["audit-prune", "--days", "0"]).exit_code != 0


def test_worker_observations_success_failure_stale_and_overlap(app, monkeypatch):
    def status():
        with app.extensions["neofab2_db"].connect() as conn:
            return operations.snapshot(app, conn)
    assert status()["worker_state"] == "never"
    mail.run_worker(app)
    assert status()["worker_state"] == "finished"
    def fail(*args):
        raise ValueError("synthetic-secret-exception")
    monkeypatch.setattr(mail, "_run_worker", fail)
    with pytest.raises(ValueError):
        mail.run_worker(app)
    assert status()["worker_state"] == "failed"
    assert "synthetic-secret" not in repr(status())
    first, second = operations.worker_started(app), operations.worker_started(app)
    operations.worker_finished(app, first, failed=True)
    assert status()["worker"]["run_id"] == second
    assert status()["worker_state"] == "running"
    started = status()["worker"]["started_at"]
    monkeypatch.setattr(operations.time, "time", lambda: started + 301)
    assert status()["worker_state"] == "stale"


def test_status_invalid_configuration_and_restart_required(app):
    client = login(app)
    change_selection(app, 1, "core_test", "disable")
    assert "Restart web and worker processes" in client.get("/admin/status").text
    with write_transaction(app) as conn:
        conn.execute(mail.settings.insert().values(key=mail.SETTING_KEY, value="bad-secret-config"))
        conn.execute(update(mail.settings).where(mail.settings.c.key == "core.plugins.enabled").values(value='["missing-secret-plugin"]'))
    page = client.get("/admin/status")
    assert page.status_code == 200
    assert "Saved plugin selection is invalid" in page.text
    assert "bad-secret-config" not in page.text and "missing-secret-plugin" not in page.text


def test_plugin_audit_permission_namespace_fresh_user_and_rollback(app):
    with app.test_request_context():
        g.current_user = {"id": 1}  # no wildcard for administrator
        with pytest.raises(PermissionError):
            record_action("core_test", "core_test.action")
        g.current_user = {"id": 2}
        before = rows(app)
        with pytest.raises(RuntimeError), write_transaction(app) as conn:
            record_action("core_test", "core_test.action", target_id=42, connection=conn)
            raise RuntimeError()
        assert rows(app) == before
        record_action("core_test", "core_test.action", target_id=42)
        assert rows(app)[-1]["module_id"] == "core_test"
        with pytest.raises(PermissionError):
            record_action("core_test", "core.settings.manage")
        with write_transaction(app) as conn:
            conn.execute(update(users).where(users.c.id == 2).values(active=False))
        with pytest.raises(PermissionError):
            record_action("core_test", "core_test.action")


def test_upgrade_0010_repeat_restart_backup_and_missing_schema(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "s"*64, "DATA_DIR": str(tmp_path)})
    try:
        with app.extensions["neofab2_db"].begin() as conn:
            config = migration_config()
            config.attributes["connection"] = conn
            command.upgrade(config, "0010_account_flows")
            conn.execute(mail.settings.insert().values(key="synthetic", value="preserve"))
        assert not database_ready(app)
        upgrade_database(app)
        upgrade_database(app)
        assert database_ready(app) and rows(app) == []
        with write_transaction(app) as conn:
            audit.record(conn, "plugins.recovered")
        mail.run_worker(app)
        with sqlite3.connect(Path(app.config["DATA_DIR"]) / "neofab2.sqlite3") as source, sqlite3.connect(tmp_path / "backup.sqlite3") as target:
            source.backup(target)
            assert target.execute("SELECT event FROM core_audit_events").fetchone() == ("plugins.recovered",)
            assert target.execute("SELECT state FROM core_worker_status").fetchone() == ("finished",)
            assert target.execute("SELECT value FROM core_settings").fetchone() == ("preserve",)
        other = create_app({"SECRET_KEY": "s"*64, "DATA_DIR": str(tmp_path)})
        try:
            assert rows(other) == rows(app)
        finally:
            other.extensions["neofab2_db"].dispose()
    finally:
        app.extensions["neofab2_db"].dispose()


def test_configuration_and_logout_events(app):
    from neofab2.core import settings, account_flows
    from neofab2.core.plugin_state import restore_config_selection
    settings.save_settings(app, 1, {**settings.DEFAULTS, "site_name": "Never log this title"})
    mail.save_settings(app, 1, mail.DEFAULTS)
    account_flows.save_policy(app, 1, account_flows.DEFAULT_POLICY)
    restore_config_selection(app)
    client = login(app)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', client.get("/profile").text).group(1)
    assert client.post("/logout", data={"csrf_token": csrf}).status_code == 302
    names = {row["event"] for row in rows(app)}
    assert {"settings.changed", "smtp.changed", "accounts.changed", "plugins.recovered", "logout"} <= names
    assert "Never log this title" not in repr(rows(app))


def test_plugin_audit_disabled_pending_and_foreign_connection(app, tmp_path):
    from sqlalchemy import create_engine
    with app.test_request_context():
        g.current_user = {"id": 2}
        other = create_engine("sqlite://")
        try:
            with other.begin() as conn, pytest.raises(ValueError):
                record_action("core_test", "core_test.action", connection=conn)
        finally:
            other.dispose()
        with write_transaction(app) as conn:
            conn.execute(update(users).where(users.c.id == 2).values(activation_pending=True))
        with pytest.raises(PermissionError):
            record_action("core_test", "core_test.action")
        with write_transaction(app) as conn:
            conn.execute(update(users).where(users.c.id == 2).values(activation_pending=False))
        change_selection(app, 1, "core_test", "disable")
        with pytest.raises(PermissionError):
            record_action("core_test", "core_test.action")
