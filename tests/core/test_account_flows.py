"""U02-U04/S06: synthetic self-service workflows, never external SMTP."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re

from alembic import command
import pytest
from sqlalchemy import select, update, func

from neofab2 import create_app
from neofab2.config import load_config
from neofab2.database import upgrade_database, database_ready, migration_config
from neofab2.core import account_flows as flows
from neofab2.core.auth import authenticate, token_hash
from neofab2.core.users import create_user, edit_user, change_password, reset_admin_password, users, sessions, write_transaction
from neofab2.services import mail

PASSWORD = "Synthetic old password!"
NEW_PASSWORD = "Synthetic new password!"
POLICY = dict(registration_enabled=True, reset_enabled=True, allow_all_domains=False, allowed_domains=["example.org"])


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    app = create_app({"SECRET_KEY": "synthetic" * 8, "DATA_DIR": str(tmp_path), "TESTING": True,
                      "SESSION_COOKIE_SECURE": False, "PUBLIC_BASE_URL": "https://workshop.example.org"})
    upgrade_database(app)
    create_user(app, "admin@example.org", "Admin", PASSWORD, "admin", bootstrap=True)
    create_user(app, "user@example.org", "User", PASSWORD, actor_id=1)
    create_user(app, "disabled@example.org", "Disabled", PASSWORD, actor_id=1, active=False)
    mail.save_settings(app, 1, {**mail.DEFAULTS, "enabled": True, "host": "smtp.example.org", "sender": "sender@example.org"})
    flows.save_policy(app, 1, POLICY)
    monkeypatch.setattr(mail, "deliver", lambda *args: pytest.fail("External transport must not be used"))
    yield app
    app.extensions["neofab2_db"].dispose()


def rows(app, table):
    with app.extensions["neofab2_db"].connect() as connection:
        return list(connection.execute(select(table)).mappings())


def user(app, email):
    return next(row for row in rows(app, users) if row["email"] == email)


def latest_code(app, purpose, email):
    user_id = user(app, email)["id"]
    candidates = [row for row in rows(app, flows.tokens) if row["purpose"] == purpose and row["user_id"] == user_id and row["used_at"] is None]
    return flows.code_for(app, candidates[-1]["id"], purpose)


def post(client, path, data, form=None, **kwargs):
    response = client.get(form or path)
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)
    return client.post(path, data={**data, "csrf_token": token}, **kwargs)


def login(app, email="admin@example.org"):
    client = app.test_client()
    assert post(client, "/login", {"email": email, "password": PASSWORD}).status_code == 302
    return client


def register(app, email="new@example.org", ip="127.0.0.1", locale="en"):
    flows.request_email(app, "register", email, ip, display_name="Synthetic Name", locale=locale)
    return latest_code(app, "activate", email)


def test_registration_activation_password_selection_and_welcome(app, monkeypatch):
    code = register(app, locale="de")
    pending = user(app, "new@example.org")
    assert not pending["active"] and pending["activation_pending"] and pending["role"] == "user"
    assert authenticate(app, "new@example.org", PASSWORD, "127.0.0.2") is None
    jobs = rows(app, mail.outbox)
    assert code not in repr(jobs) + repr(rows(app, flows.tokens))
    messages = []
    monkeypatch.setattr(mail, "deliver", lambda config, password, job: (messages.append(job) or ("sent", None)))
    assert mail.run_worker(app)["sent"] == 1
    assert code in messages[0]["body"] and "Konto aktivieren" in messages[0]["subject"]
    assert "https://workshop.example.org/activate" in messages[0]["body"]
    assert "?" not in messages[0]["body"]
    flows.redeem(app, "activate", code, NEW_PASSWORD, "127.0.0.1")
    active = user(app, "new@example.org")
    assert active["active"] and not active["activation_pending"]
    assert authenticate(app, "new@example.org", NEW_PASSWORD, "127.0.0.2")
    assert mail.run_worker(app)["sent"] == 1
    assert "Willkommen" in messages[-1]["subject"] and NEW_PASSWORD not in repr(messages)
    with pytest.raises(ValueError, match="invalid, expired"):
        flows.redeem(app, "activate", code, "Other synthetic password", "127.0.0.1")


def test_reset_revokes_all_sessions_and_does_not_reactivate_disabled(app):
    sessions_before = [authenticate(app, "user@example.org", PASSWORD, f"ip-{i}") for i in range(2)]
    old_hash = user(app, "user@example.org")["password_hash"]
    flows.request_email(app, "reset", "user@example.org", "one")
    assert user(app, "user@example.org")["password_hash"] == old_hash
    assert len(rows(app, sessions)) == 2
    code = latest_code(app, "reset", "user@example.org")
    flows.redeem(app, "reset", code, NEW_PASSWORD, "one")
    assert not any(row["token_hash"] in [token_hash(t) for t in sessions_before] for row in rows(app, sessions))
    assert authenticate(app, "user@example.org", PASSWORD, "two") is None
    assert authenticate(app, "user@example.org", NEW_PASSWORD, "two")
    flows.request_email(app, "reset", "disabled@example.org", "one")
    assert not any(row["user_id"] == 3 for row in rows(app, flows.tokens))
    assert not user(app, "disabled@example.org")["active"]
    notices = [row for row in rows(app, mail.outbox) if row["account_token_id"] is None]
    assert len(notices) == 1 and NEW_PASSWORD not in notices[0]["body"]


@pytest.mark.parametrize("purpose", ["activate", "reset"])
def test_expired_wrong_purpose_and_tampered_codes(app, monkeypatch, purpose):
    if purpose == "activate":
        code = register(app)
    else:
        flows.request_email(app, "reset", "user@example.org", "one")
        code = latest_code(app, "reset", "user@example.org")
    for wrong in (code[:-1] + ("0" if code[-1] != "0" else "1"), "invalid"):
        with pytest.raises(ValueError):
            flows.redeem(app, purpose, wrong, NEW_PASSWORD, "one")
    with pytest.raises(ValueError):
        flows.redeem(app, "reset" if purpose == "activate" else "activate", code, NEW_PASSWORD, "one")
    expiry = rows(app, flows.tokens)[0]["expires_at"]
    monkeypatch.setattr(flows.time, "time", lambda: expiry)
    with pytest.raises(ValueError):
        flows.redeem(app, purpose, code, NEW_PASSWORD, "one")
    assert mail.run_worker(app)["failed"] == 1
    assert rows(app, mail.outbox)[0]["error_code"] == "account_request_invalid"


def test_domain_rules_closed_default_and_corrupt_policy(app):
    for email in ("new@other.org", "new@sub.example.org"):
        flows.request_email(app, "register", email, "one", display_name="Synthetic")
    assert len(rows(app, users)) == 3
    flows.save_policy(app, 1, {**POLICY, "allow_all_domains": True})
    register(app, email="new@other.org")
    flows.save_policy(app, 1, flows.DEFAULT_POLICY)
    with pytest.raises(ValueError):
        register(app, email="other@example.org")
    with write_transaction(app) as connection:
        connection.execute(update(flows.settings).where(flows.settings.c.key == flows.POLICY_KEY).values(value='{"registration_enabled": true}'))
    assert app.test_client().get("/register").status_code == 403


@pytest.mark.parametrize("patch", [
    {"allowed_domains": []}, {"allowed_domains": ["*.example.org"]},
    {"allowed_domains": ["https://example.org"]}, {"registration_enabled": "yes"}, {"role": "admin"},
])
def test_invalid_policy_is_atomic(app, patch):
    with pytest.raises(ValueError):
        flows.save_policy(app, 1, {**POLICY, **patch})
    with app.extensions["neofab2_db"].connect() as conn:
        assert flows.read_policy(conn) == POLICY


def test_enabling_requires_origin_smtp_and_admin(app):
    with pytest.raises(PermissionError):
        flows.save_policy(app, 2, POLICY)
    app.config["PUBLIC_BASE_URL"] = ""
    with pytest.raises(ValueError):
        flows.save_policy(app, 1, POLICY)
    app.config["PUBLIC_BASE_URL"] = "https://workshop.example.org"
    mail.save_settings(app, 1, mail.DEFAULTS)
    with pytest.raises(ValueError):
        flows.save_policy(app, 1, POLICY)
    flows.save_policy(app, 1, flows.DEFAULT_POLICY)


def test_duplicate_registration_generic_responses_and_no_role_injection(app):
    client = app.test_client()
    data = {"email": "new@example.org", "display_name": "Synthetic", "role": "admin", "active": "on", "password": PASSWORD}
    assert post(client, "/register", data).status_code == 302
    before = user(app, "new@example.org")
    assert post(client, "/register", {**data, "display_name": "Overwrite"}).status_code == 302
    assert dict(user(app, "new@example.org")) == dict(before)
    assert before["role"] == "user" and not before["active"]
    assert len(rows(app, flows.tokens)) == 1
    responses = []
    for address in ("user@example.org", "missing@example.org", "disabled@example.org"):
        result = post(client, "/forgot-password", {"email": address}, follow_redirects=True)
        assert result.status_code == 200
        responses.append(flows.GENERIC in result.text)
    assert all(responses)


def test_csrf_get_does_not_consume_code_and_no_secret_echo(app):
    code = register(app)
    client = app.test_client()
    for path in ("/register", "/activate", "/reset-password", "/forgot-password", "/activation-request"):
        assert client.get(path).status_code == 200
        assert client.post(path, data={"code": code}).status_code == 400
    assert client.get("/activate", query_string={"code": code}).status_code == 200
    assert rows(app, flows.tokens)[0]["used_at"] is None
    response = post(client, "/activate", {"code": code, "new_password": NEW_PASSWORD, "confirm_password": "different"})
    assert response.status_code == 400 and code not in response.text and NEW_PASSWORD not in response.text
    response = post(client, "/activate", {"code": code, "new_password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD})
    assert response.status_code == 302 and response.location == "/login"
    assert client.get("/profile").location == "/login"


def test_admin_page_permissions_csrf_and_pending_account_status(app):
    assert app.test_client().get("/admin/settings/accounts").location == "/login"
    ordinary = login(app, "user@example.org")
    assert ordinary.get("/admin/settings/accounts").status_code == 403
    assert post(ordinary, "/admin/settings/accounts", {}, form="/profile").status_code == 403
    admin = login(app)
    assert admin.post("/admin/settings/accounts", data={}).status_code == 400
    assert post(admin, "/admin/settings/accounts", {"allowed_domains": "example.org", "registration_enabled": "on"}).status_code == 302
    code = register(app)
    pending = user(app, "new@example.org")
    assert "awaiting email activation" in admin.get(f"/admin/users/{pending['id']}/edit").text
    with pytest.raises(ValueError, match="initial password"):
        edit_user(app, pending["id"], pending["email"], "Name", "user", True, actor_id=1)
    edit_user(app, pending["id"], pending["email"], "Name", "user", False, actor_id=1)
    assert not user(app, pending["email"])["activation_pending"]
    with pytest.raises(ValueError):
        flows.redeem(app, "activate", code, NEW_PASSWORD, "one")


@pytest.mark.parametrize("action", ["profile-password", "admin-password", "email", "disable-enable", "role"])
def test_existing_reset_codes_revoked_by_security_changes(app, action):
    flows.request_email(app, "reset", "user@example.org", "one")
    code = latest_code(app, "reset", "user@example.org")
    if action == "profile-password":
        change_password(app, 2, PASSWORD, NEW_PASSWORD)
    else:
        edit_user(app, 2, "changed@example.org" if action == "email" else "user@example.org", "User",
                  "staff" if action == "role" else "user", action != "disable-enable", actor_id=1,
                  new_password=NEW_PASSWORD if action == "admin-password" else "")
        if action == "disable-enable":
            edit_user(app, 2, "user@example.org", "User", "user", True, actor_id=1)
    with pytest.raises(ValueError):
        flows.redeem(app, "reset", code, "Yet another synthetic password", "one")
    assert mail.run_worker(app)["failed"] == 1


def test_local_admin_recovery_invalidates_email_reset(app):
    flows.request_email(app, "reset", "admin@example.org", "one")
    code = latest_code(app, "reset", "admin@example.org")
    reset_admin_password(app, 1, NEW_PASSWORD)
    with pytest.raises(ValueError):
        flows.redeem(app, "reset", code, "Other synthetic password", "one")


def test_resend_cooldown_limits_and_revocation(app, monkeypatch):
    now = 100000
    monkeypatch.setattr(flows.time, "time", lambda: now)
    original = register(app)
    flows.request_email(app, "activate", "new@example.org", "one")
    assert len(rows(app, flows.tokens)) == 1
    now += 61
    flows.request_email(app, "activate", "new@example.org", "one")
    new = latest_code(app, "activate", "new@example.org")
    assert new != original
    now += 61
    flows.request_email(app, "activate", "new@example.org", "one")
    assert len(rows(app, flows.tokens)) == 2  # three requests per address already used
    with pytest.raises(ValueError):
        flows.redeem(app, "activate", original, NEW_PASSWORD, "one")
    flows.redeem(app, "activate", new, NEW_PASSWORD, "one")


def test_ip_limit_and_unknown_address_privacy(app):
    for number in range(21):
        flows.request_email(app, "register", f"new{number}@example.org", "same-ip", display_name="Synthetic")
    assert len(rows(app, flows.tokens)) == 20
    stored = rows(app, flows.limits)
    assert "same-ip" not in repr(stored) and "@example.org" not in repr(stored)


def test_concurrent_redemption_only_once(app):
    code = register(app)
    def run(number):
        try:
            flows.redeem(app, "activate", code, NEW_PASSWORD, f"ip-{number}")
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, range(2))) == [False, True]
    assert len([job for job in rows(app, mail.outbox) if job["account_token_id"] is None]) == 1


def test_atomic_queue_failure_rolls_back_account_and_activation(app, monkeypatch):
    original = mail.enqueue
    def failing(*args, **kwargs):
        raise RuntimeError("synthetic queue failure")
    monkeypatch.setattr(mail, "enqueue", failing)
    with pytest.raises(RuntimeError):
        register(app)
    assert len(rows(app, users)) == 3 and not rows(app, flows.tokens)
    monkeypatch.setattr(mail, "enqueue", original)
    code = register(app)
    monkeypatch.setattr(mail, "enqueue", failing)
    with pytest.raises(RuntimeError):
        flows.redeem(app, "activate", code, NEW_PASSWORD, "one")
    assert not user(app, "new@example.org")["active"] and rows(app, flows.tokens)[0]["used_at"] is None


def test_canonical_origin_ignores_host_header_and_codes_not_in_database(app, monkeypatch):
    client = app.test_client()
    headers = {"Host": "evil.example.org"}
    page = client.get("/register", headers=headers)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    assert client.post("/register", data={"email": "new@example.org", "display_name": "Synthetic", "csrf_token": csrf}, headers=headers).status_code == 302
    code = latest_code(app, "activate", "new@example.org")
    sent = []
    monkeypatch.setattr(mail, "deliver", lambda config, password, job: (sent.append(job) or ("sent", None)))
    mail.run_worker(app)
    assert "evil.example.org" not in sent[0]["body"] and "https://workshop.example.org" in sent[0]["body"]
    assert code.encode() not in (Path(app.config["DATA_DIR"]) / "neofab2.sqlite3").read_bytes()


@pytest.mark.parametrize("origin", ["https://user:password@example.org", "https://example.org/path", "https://example.org?x=1", "https://example.org/#code", "javascript:bad", "http://example.org", "https://example.org\n"])
def test_invalid_public_origin_rejected(tmp_path, monkeypatch, origin):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    with pytest.raises(ValueError):
        load_config({"SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path), "PUBLIC_BASE_URL": origin})


def test_restart_and_schema_upgrade_preserve_disabled_accounts(app, tmp_path):
    code = register(app)
    other = create_app({key: app.config[key] for key in ("SECRET_KEY", "DATA_DIR", "PUBLIC_BASE_URL", "SESSION_COOKIE_SECURE")})
    try:
        flows.redeem(other, "activate", code, NEW_PASSWORD, "one")
        assert not user(other, "disabled@example.org")["active"]
    finally:
        other.extensions["neofab2_db"].dispose()
    old_path = tmp_path / "old"
    old_path.mkdir()
    old = create_app({"SECRET_KEY": "s" * 64, "DATA_DIR": str(old_path)})
    try:
        with old.extensions["neofab2_db"].begin() as conn:
            config = migration_config()
            config.attributes["connection"] = conn
            command.upgrade(config, "0009_mail_outbox")
            conn.exec_driver_sql("INSERT INTO core_users (email,display_name,password_hash,role,active,created_at) VALUES ('old@example.org','Synthetic','unusable','user',0,0)")
        assert not database_ready(old)
        upgrade_database(old)
        upgrade_database(old)
        assert database_ready(old)
        assert not user(old, "old@example.org")["activation_pending"]
        assert not user(old, "old@example.org")["active"]
        with old.extensions["neofab2_db"].connect() as conn:
            assert flows.read_policy(conn) == flows.DEFAULT_POLICY
    finally:
        old.extensions["neofab2_db"].dispose()


def test_policy_shutdown_revokes_codes_even_after_reenable(app):
    activation = register(app)
    flows.request_email(app, "reset", "user@example.org", "one")
    reset = latest_code(app, "reset", "user@example.org")
    flows.save_policy(app, 1, flows.DEFAULT_POLICY)
    flows.save_policy(app, 1, POLICY)
    for purpose, code in (("activate", activation), ("reset", reset)):
        with pytest.raises(ValueError):
            flows.redeem(app, purpose, code, NEW_PASSWORD, "one")
    assert user(app, "new@example.org")["activation_pending"]


def test_existing_account_reset_not_subject_to_registration_domains(app):
    create_user(app, "external@other.org", "Synthetic", PASSWORD, actor_id=1)
    flows.request_email(app, "reset", "external@other.org", "one")
    flows.redeem(app, "reset", latest_code(app, "reset", "external@other.org"), NEW_PASSWORD, "one")
    assert authenticate(app, "external@other.org", NEW_PASSWORD, "two")


def test_french_email_and_german_public_pages(app, monkeypatch):
    code = register(app, locale="fr")
    sent = []
    monkeypatch.setattr(mail, "deliver", lambda config, password, job: (sent.append(job) or ("sent", None)))
    assert mail.run_worker(app)["sent"] == 1
    assert "Activez votre compte" in sent[0]["subject"] and code in sent[0]["body"]
    client = app.test_client()
    with client.session_transaction() as session:
        session["locale"] = "de"
    assert "Registrieren" in client.get("/register").text
    assert "Code aus der E-Mail" in client.get("/activate").text


def test_smtp_pause_does_not_lose_pending_registration(app):
    mail.save_settings(app, 1, mail.DEFAULTS)
    register(app)
    assert sum(mail.run_worker(app).values()) == 0
    assert rows(app, mail.outbox)[0]["attempts"] == 0
    assert user(app, "new@example.org")["activation_pending"]


def test_parallel_registration_has_one_account_and_one_job(app):
    def submit(number):
        flows.request_email(app, "register", "new@example.org", f"ip-{number}", display_name="Synthetic")
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(submit, range(2)))
    assert len(rows(app, users)) == 4 and len(rows(app, flows.tokens)) == 1 and len(rows(app, mail.outbox)) == 1


def test_backup_restores_pending_code_and_account(app, tmp_path):
    import sqlite3
    code = register(app)
    restored_path = tmp_path / "restored"
    restored_path.mkdir()
    with sqlite3.connect(Path(app.config["DATA_DIR"]) / "neofab2.sqlite3") as source, sqlite3.connect(restored_path / "neofab2.sqlite3") as target:
        source.backup(target)
    restored = create_app({"SECRET_KEY": app.config["SECRET_KEY"], "DATA_DIR": str(restored_path), "PUBLIC_BASE_URL": app.config["PUBLIC_BASE_URL"]})
    try:
        assert database_ready(restored)
        flows.redeem(restored, "activate", code, NEW_PASSWORD, "one")
        assert user(restored, "new@example.org")["active"]
        assert not user(app, "new@example.org")["active"]
    finally:
        restored.extensions["neofab2_db"].dispose()


def test_secret_change_invalidates_pending_code(app):
    code = register(app)
    app.config["SECRET_KEY"] = "changed-synthetic-key" * 4
    with pytest.raises(ValueError):
        flows.redeem(app, "activate", code, NEW_PASSWORD, "one")
    assert mail.run_worker(app)["failed"] == 1


def test_http_origin_only_in_explicit_http_test_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    config = load_config({"SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path),
                          "SESSION_COOKIE_SECURE": False, "PUBLIC_BASE_URL": "http://localhost:5000/"})
    assert config["PUBLIC_BASE_URL"] == "http://localhost:5000"


def test_international_domain_matches_ascii_smtp_recipient(app, monkeypatch):
    flows.save_policy(app, 1, {**POLICY, "allowed_domains": ["bücher.de"]})
    code = register(app, email="new@bücher.de")
    sent = []
    monkeypatch.setattr(mail, "deliver", lambda config, password, job: (sent.append(job) or ("sent", None)))
    assert mail.run_worker(app)["sent"] == 1
    assert sent[0]["recipient"] == "new@xn--bcher-kva.de" and code in sent[0]["body"]
    flows.redeem(app, "activate", code, NEW_PASSWORD, "one")
    assert mail.run_worker(app)["sent"] == 1
