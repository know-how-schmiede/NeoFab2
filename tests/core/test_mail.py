"""S05/S06/N05: synthetic jobs, mocked SMTP, no external mail."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import re
import smtplib
import sqlite3

from alembic import command
from flask import g
import pytest
from sqlalchemy import select, update

from neofab2 import create_app
from neofab2.core.users import create_user, users, write_transaction
from neofab2.core.plugin_state import change_selection
from neofab2.database import database_ready, migration_config, upgrade_database
from neofab2.plugin_api import Permission
from neofab2.plugin_api.notifications import enqueue_email
from neofab2.plugin_api.registry import Registry
from neofab2.plugins.core_test import plugin
from neofab2.services import mail

PATH = "/admin/settings/mail"
CONFIG = {**mail.DEFAULTS, "enabled": True, "host": "smtp.example.org", "sender": "sender@example.org"}
TEST_PLUGIN = replace(plugin, permissions=(Permission("core_test.mail", ("staff",)),),
                      roles=("user", "staff", "admin"), mail_permission="core_test.mail")


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"TESTING": True, "SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path),
                      "SESSION_COOKIE_SECURE": False, "SMTP_PASSWORD": "synthetic-secret",
                      "ENABLED_PLUGINS": ["core_test"]}, plugins=[TEST_PLUGIN])
    upgrade_database(app)
    create_user(app, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    for role in ("user", "staff"):
        create_user(app, f"{role}@example.org", role, "Test123!", role, actor_id=1)
    yield app
    app.extensions["neofab2_db"].dispose()


def enqueue(app, key="one", module="core"):
    with write_transaction(app) as conn:
        return mail.enqueue(conn, module, key, "recipient@example.org", "Synthetic subject", "Synthetic body")


def row(app, job):
    with app.extensions["neofab2_db"].connect() as conn:
        return dict(conn.execute(select(mail.outbox).where(mail.outbox.c.id == job)).mappings().one())


def post(client, path, data, form=None):
    token = re.search(r'name="csrf_token" value="([^"]+)"', client.get(form or path).text).group(1)
    return client.post(path, data={**data, "csrf_token": token})


def login(app, role):
    client = app.test_client()
    assert post(client, "/login", {"email": f"{role}@example.org", "password": "Test123!"}).status_code == 302
    return client


def test_admin_ui_secret_csrf_and_test_idempotency(app):
    assert app.test_client().get(PATH).location == "/login"
    for role in ("user", "staff"):
        client = login(app, role)
        assert client.get(PATH).status_code == 403
        assert post(client, PATH, {"action": "test"}, "/profile").status_code == 403
    client = login(app, "admin")
    assert client.post(PATH, data={"action": "test"}).status_code == 400
    assert post(client, PATH, {**CONFIG, "enabled": "on", "action": "save"}).status_code == 302
    page = client.get(PATH)
    assert page.status_code == 200 and "synthetic-secret" not in page.text
    assert "smtp.example.org" in page.text and '<svg' in page.text
    key = re.search(r'name="request_key" value="([^"]+)"', page.text).group(1)
    data = {"action": "test", "request_key": key, "recipient": "test@example.org"}
    assert post(client, PATH, data).status_code == 302
    assert post(client, PATH, data).status_code == 302
    with app.extensions["neofab2_db"].connect() as conn:
        jobs = conn.execute(select(mail.outbox)).mappings().all()
        assert len(jobs) == 1 and jobs[0]["status"] == "queued"
        assert "synthetic-secret" not in conn.execute(select(mail.settings.c.value)).scalar_one()
    assert post(client, PATH, {**CONFIG, "enabled": "on", "action": "save", "SMTP_PASSWORD": "inject"}).status_code == 400


@pytest.mark.parametrize("patch", [{"port": 0}, {"mode": "bad"}, {"sender": "x\r\nBcc: victim@example.org"},
    {"host": "https://secret@example.org"}, {"username": "user", "mode": "plain"}, {"enabled": "yes"}])
def test_invalid_settings_preserve_previous(app, patch):
    mail.save_settings(app, 1, CONFIG)
    with pytest.raises(ValueError):
        mail.save_settings(app, 1, {**CONFIG, **patch})
    with app.extensions["neofab2_db"].connect() as conn:
        assert mail.read_settings(conn) == CONFIG


def test_idempotency_atomic_rollback_and_restart(app):
    job = enqueue(app)
    assert enqueue(app) == job
    with pytest.raises(ValueError), write_transaction(app) as conn:
        mail.enqueue(conn, "core", "one", "other@example.org", "Synthetic subject", "Synthetic body")
    with pytest.raises(RuntimeError), write_transaction(app) as conn:
        mail.enqueue(conn, "core", "rollback", "recipient@example.org", "Subject", "Body")
        raise RuntimeError("rollback")
    other = create_app({key: app.config[key] for key in ("SECRET_KEY", "DATA_DIR", "ENABLED_PLUGINS")}, plugins=[TEST_PLUGIN])
    try:
        assert row(other, job)["status"] == "queued"
        with other.extensions["neofab2_db"].connect() as conn:
            assert len(conn.execute(select(mail.outbox)).all()) == 1
    finally:
        other.extensions["neofab2_db"].dispose()


def test_disabled_smtp_and_plugin_do_not_consume_attempts(app, monkeypatch):
    def forbidden(*args):
        pytest.fail("Transport must not run")
    monkeypatch.setattr(mail, "deliver", forbidden)
    job = enqueue(app, module="core_test")
    assert sum(mail.run_worker(app).values()) == 0
    mail.save_settings(app, 1, CONFIG)
    change_selection(app, 1, "core_test", "disable")
    assert sum(mail.run_worker(app).values()) == 0
    assert row(app, job)["attempts"] == 0
    change_selection(app, 1, "core_test", "enable")
    monkeypatch.setattr(mail, "deliver", lambda *args: ("sent", None))
    assert mail.run_worker(app)["sent"] == 1


def test_retries_bounded_manual_retry_and_no_sent_replay(app, monkeypatch):
    monkeypatch.setattr(mail.time, "time", lambda: 1000)
    job = enqueue(app)
    mail.save_settings(app, 1, CONFIG)
    monkeypatch.setattr(mail, "deliver", lambda *args: ("retry", "connection_failed"))
    for attempt in range(1, 6):
        due = row(app, job)["next_attempt_at"]
        monkeypatch.setattr(mail.time, "time", lambda: due)
        counts = mail.run_worker(app)
        assert counts["retry" if attempt < 5 else "failed"] == 1
        assert row(app, job)["attempts"] == attempt
        if attempt < 5:
            assert row(app, job)["next_attempt_at"] == due + 60 * 2 ** (attempt - 1)
        assert sum(mail.run_worker(app).values()) == 0
    with pytest.raises(PermissionError):
        mail.retry_job(app, 2, job)
    mail.retry_job(app, 1, job)
    monkeypatch.setattr(mail, "deliver", lambda *args: ("sent", None))
    assert mail.run_worker(app)["sent"] == 1
    assert row(app, job)["total_attempts"] == 6
    with pytest.raises(ValueError):
        mail.retry_job(app, 1, job)
    assert sum(mail.run_worker(app).values()) == 0


def test_concurrent_claim_and_expired_lease_require_acknowledgement(app, monkeypatch):
    mail.save_settings(app, 1, CONFIG)
    job = enqueue(app)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claimed = list(pool.map(lambda _: mail.claim(app), range(2)))
    assert sum(item is not None for item in claimed) == 1
    with pytest.raises(ValueError):
        mail.retry_job(app, 1, job, acknowledge=True)
    expires = row(app, job)["lease_until"]
    monkeypatch.setattr(mail.time, "time", lambda: expires)
    assert mail.claim(app) is None
    assert row(app, job)["status"] == "uncertain"
    with pytest.raises(ValueError):
        mail.retry_job(app, 1, job)
    mail.retry_job(app, 1, job, acknowledge=True)
    assert row(app, job)["status"] == "queued"


def test_plugin_action_permission_fresh_user_and_transaction(app):
    with app.test_request_context():
        for user_id in (1, 2):  # admin has no wildcard for staff-only action
            g.current_user = {"id": user_id}
            with pytest.raises(PermissionError):
                enqueue_email("core_test", "denied", "recipient@example.org", "Subject", "Body")
        g.current_user = {"id": 3}
        with pytest.raises(RuntimeError), write_transaction(app) as conn:
            enqueue_email("core_test", "rollback", "recipient@example.org", "Subject", "Body", connection=conn)
            raise RuntimeError()
        job = enqueue_email("core_test", "ok", "recipient@example.org", "Subject", "Body")
        assert row(app, job)["module_id"] == "core_test"
        with write_transaction(app) as conn:
            conn.execute(update(users).where(users.c.id == 3).values(active=False))
        with pytest.raises(PermissionError):
            enqueue_email("core_test", "inactive", "recipient@example.org", "Subject", "Body")
    with pytest.raises(ValueError):
        Registry([replace(TEST_PLUGIN, mail_permission="core_test.undeclared")], ["core_test"])


class FakeSMTP:
    def __init__(self, **kwargs):
        self.calls = []
        self.error = None
        self.stage = "data"
    def connect(self, *args):
        if self.stage == "connect" and self.error:
            raise self.error
        return 220, b"ready"
    def ehlo_or_helo_if_needed(self): pass
    def ehlo(self): pass
    def starttls(self, **kwargs): self.calls.append("tls")
    def login(self, *args): self.calls.append("login")
    def mail(self, sender): return 250, b"ok"
    def rcpt(self, recipient): return 250, b"ok"
    def data(self, content):
        self.content = content
        if self.error: raise self.error
        return 250, b"ok"
    def close(self): self.calls.append("closed")


@pytest.mark.parametrize("stage,error,expected", [
    ("connect", OSError("synthetic-secret"), "retry"),
    ("data", OSError("synthetic-secret"), "uncertain"),
    ("data", smtplib.SMTPDataError(451, b"synthetic-secret"), "retry"),
    ("data", smtplib.SMTPDataError(550, b"synthetic-secret"), "failed"),
    ("data", None, "sent"),
])
def test_transport_tls_and_sanitized_results(app, monkeypatch, caplog, stage, error, expected):
    smtp = FakeSMTP()
    smtp.stage, smtp.error = stage, error
    def factory(**kwargs):
        assert kwargs["host"] == CONFIG["host"] and kwargs["port"] == CONFIG["port"]
        smtp.connect()
        return smtp
    monkeypatch.setattr(mail.smtplib, "SMTP", factory)
    job = row(app, enqueue(app))
    result = mail.deliver({**CONFIG, "username": "synthetic-user"}, "synthetic-secret", job)
    assert result[0] == expected
    assert "synthetic-secret" not in repr(result) + caplog.text
    if stage == "data":
        assert smtp.calls[-1] == "closed"
        assert smtp.calls[:2] == ["tls", "login"]
        assert f"neofab2-{job['id']}".encode() in smtp.content
        assert "synthetic-secret".encode() not in smtp.content


def test_upgrade_from_0008_preserves_rows_and_backup(app, tmp_path):
    old = create_app({"SECRET_KEY": "x" * 64, "DATA_DIR": str(tmp_path / "old")})
    (tmp_path / "old").mkdir()
    try:
        with old.extensions["neofab2_db"].begin() as conn:
            config = migration_config()
            config.attributes["connection"] = conn
            command.upgrade(config, "0008_core_files")
            conn.execute(mail.settings.insert().values(key="synthetic", value="preserve"))
        assert not database_ready(old)
        upgrade_database(old)
        upgrade_database(old)
        assert database_ready(old)
        with old.extensions["neofab2_db"].connect() as conn:
            assert conn.execute(select(mail.settings.c.value)).scalar_one() == "preserve"
        job = enqueue(old)
        with sqlite3.connect(tmp_path / "old" / "neofab2.sqlite3") as source, sqlite3.connect(tmp_path / "copy.sqlite3") as target:
            source.backup(target)
            assert target.execute("SELECT id, status FROM core_mail_outbox").fetchone() == (job, "queued")
    finally:
        old.extensions["neofab2_db"].dispose()


def test_cli_disabled_worker_and_limit(app, monkeypatch):
    from click.testing import CliRunner
    from neofab2.cli import main
    monkeypatch.setattr("neofab2.cli.ready_app", lambda: app)
    job = enqueue(app)
    result = CliRunner().invoke(main, ["mail-worker", "--limit", "1"])
    assert result.exit_code == 0, result.output
    assert "sent=0" in result.output and row(app, job)["attempts"] == 0
    assert CliRunner().invoke(main, ["mail-worker", "--limit", "0"]).exit_code != 0


@pytest.mark.parametrize("mode", ["ssl", "plain"])
def test_ssl_and_local_relay(app, monkeypatch, mode):
    smtp = FakeSMTP()
    def factory(**kwargs):
        assert kwargs["timeout"] == 10
        assert kwargs["host"] == CONFIG["host"] and kwargs["port"] == CONFIG["port"]
        if mode == "ssl":
            assert kwargs["context"].check_hostname
        return smtp
    monkeypatch.setattr(mail.smtplib, "SMTP_SSL" if mode == "ssl" else "SMTP", factory)
    assert mail.deliver({**CONFIG, "mode": mode}, "unused", row(app, enqueue(app)))[0] == "sent"
    assert smtp.calls == ["closed"]


@pytest.mark.parametrize("recipient,subject,body", [
    ("a@example.org,b@example.org", "Subject", "Body"),
    ("a@example.org", "Subject\r\nBcc: b@example.org", "Body"),
    ("a@example.org", "Subject", "x" * 65537),
], ids=["multiple-recipients", "header-injection", "oversized-body"])
def test_message_validation_before_storage(app, recipient, subject, body):
    with pytest.raises(ValueError), write_transaction(app) as conn:
        mail.enqueue(conn, "core", "bad", recipient, subject, body)
    with app.extensions["neofab2_db"].connect() as conn:
        assert not conn.execute(select(mail.outbox)).all()


def test_uncertain_retry_ui_translation_and_pagination(app):
    job = enqueue(app)
    with write_transaction(app) as conn:
        conn.execute(update(mail.outbox).where(mail.outbox.c.id == job).values(status="uncertain", error_code="delivery_unknown"))
        for number in range(26):
            mail.enqueue(conn, "core", f"page-{number}", "recipient@example.org", "Subject", "Body")
        conn.execute(update(users).where(users.c.id == 1).values(locale="de"))
    client = login(app, "admin")
    assert "SMTP &amp; Versandaufträge" in client.get(PATH).text
    assert "Nächste Seite" in client.get(PATH).text
    assert "Vorherige Seite" in client.get(PATH + "?page=2").text
    assert post(client, PATH, {"action": "retry", "job_id": job}).status_code == 400
    assert row(app, job)["status"] == "uncertain"
    assert post(client, PATH, {"action": "retry", "job_id": job, "acknowledge": "on"}).status_code == 302
    assert row(app, job)["status"] == "queued"


def test_corrupt_configuration_and_missing_password_pause_safely(app):
    app.config["SMTP_PASSWORD"] = ""
    with pytest.raises(ValueError):
        mail.save_settings(app, 1, {**CONFIG, "username": "test"})
    job = enqueue(app)
    with write_transaction(app) as conn:
        conn.execute(mail.settings.insert().values(key=mail.SETTING_KEY, value='null'))
    with pytest.raises(ValueError):
        mail.run_worker(app)
    assert row(app, job)["attempts"] == 0
    client = login(app, "admin")
    assert client.get(PATH).status_code == 400
    assert post(client, PATH, {**CONFIG, "action": "save", "enabled": "on"}).status_code == 302


def test_late_worker_cannot_overwrite_new_attempt(app, monkeypatch):
    job = enqueue(app)
    mail.save_settings(app, 1, CONFIG)
    def interrupted(config, password, claimed):
        monkeypatch.setattr(mail.time, "time", lambda: claimed["lease_until"])
        assert mail.claim(app) is None
        mail.retry_job(app, 1, job, acknowledge=True)
        assert mail.claim(app) is not None
        return "sent", None
    monkeypatch.setattr(mail, "deliver", interrupted)
    assert sum(mail.run_worker(app, limit=1).values()) == 0
    assert row(app, job)["status"] == "sending"
    assert row(app, job)["total_attempts"] == 2


def test_standard_library_constructor_preserves_tls_hostname(app, monkeypatch):
    # Exercise constructor and connect; Python versions set _host in either.
    def get_socket(client, host, port, timeout):
        assert client._host == host == CONFIG["host"]
        client.calls = []
        return object()
    monkeypatch.setattr(mail.smtplib.SMTP, "_get_socket", get_socket)
    monkeypatch.setattr(mail.smtplib.SMTP, "getreply", lambda self: (220, b"ready"))
    for name in ("ehlo_or_helo_if_needed", "ehlo", "starttls", "mail", "rcpt", "data", "close"):
        monkeypatch.setattr(mail.smtplib.SMTP, name, getattr(FakeSMTP, name))
    monkeypatch.setattr(mail.smtplib.SMTP, "error", None, raising=False)
    assert mail.deliver(CONFIG, "", row(app, enqueue(app)))[0] == "sent"


@pytest.mark.parametrize("enabled", [False, True])
def test_relay_port_survives_save_activation_and_restart(app, enabled):
    client = login(app, "admin")
    relay = {**CONFIG, "host": "192.0.2.25", "port": 25, "mode": "plain", "enabled": enabled}
    form = {**relay, "action": "save"}
    if enabled:
        form["enabled"] = "on"
    else:
        del form["enabled"]
    assert post(client, PATH, form).status_code == 302
    # A second save exercises the update path, not just the initial insert.
    form["enabled"] = "on"
    assert post(client, PATH, form).status_code == 302
    page = client.get(PATH).text
    assert re.search(r'id="port"[^>]*value="25"', page)
    assert '<option value="plain" selected>' in page
    other = create_app({key: app.config[key] for key in ("SECRET_KEY", "DATA_DIR", "ENABLED_PLUGINS")}, plugins=[TEST_PLUGIN])
    try:
        with other.extensions["neofab2_db"].connect() as conn:
            assert mail.read_settings(conn) == {**relay, "enabled": True}
    finally:
        other.extensions["neofab2_db"].dispose()


def test_invalid_activation_keeps_submitted_port_without_saving(app):
    client = login(app, "admin")
    form = {**CONFIG, "action": "save", "enabled": "on", "port": "25", "mode": "plain", "sender": ""}
    response = post(client, PATH, form)
    assert response.status_code == 400
    assert re.search(r'id="port"[^>]*value="25"', response.text)
    assert '<option value="plain" selected>' in response.text
    assert 'Sending is paused.' in response.text
    with app.extensions["neofab2_db"].connect() as conn:
        assert mail.read_settings(conn) == mail.DEFAULTS


def test_plain_relay_over_real_socket(app):
    """Real smtplib conversation; loopback only, no external SMTP or mailbox."""
    from socketserver import TCPServer, StreamRequestHandler
    from threading import Thread

    commands, messages = [], []

    class Relay(StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(5)
            self.wfile.write(b"220 synthetic relay\r\n")
            while line := self.rfile.readline():
                commands.append(line)
                verb = line.split(b" ", 1)[0].strip().upper()
                if verb in (b"EHLO", b"HELO", b"MAIL", b"RCPT"):
                    self.wfile.write(b"250 OK\r\n")
                elif verb == b"DATA":
                    self.wfile.write(b"354 send data\r\n")
                    body = []
                    while (line := self.rfile.readline()) not in (b".\r\n", b""):
                        body.append(line)
                    messages.append(b"".join(body))
                    self.wfile.write(b"250 accepted\r\n")
                else:
                    self.wfile.write(b"500 unsupported\r\n")

    with TCPServer(("127.0.0.1", 0), Relay) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            app.config["SMTP_PASSWORD"] = ""
            client = login(app, "admin")
            settings = {**CONFIG, "host": "127.0.0.1", "port": server.server_address[1], "mode": "plain"}
            assert post(client, PATH, {**settings, "enabled": "on", "action": "save"}).status_code == 302
            key = re.search(r'name="request_key" value="([^"]+)"', client.get(PATH).text).group(1)
            assert post(client, PATH, {"action": "test", "request_key": key, "recipient": "recipient@example.org"}).status_code == 302
            assert mail.run_worker(app) == dict(sent=1, retry=0, failed=0, uncertain=0)
            assert sum(mail.run_worker(app).values()) == 0
            assert len(messages) == 1
            assert b"Subject: NeoFab2 SMTP-Test" in messages[0]
            assert not any(c.startswith((b"STARTTLS", b"AUTH")) for c in commands)
            assert b"mail from:<sender@example.org>\r\n" in [c.lower() for c in commands]
        finally:
            server.shutdown()
            thread.join(timeout=5)
