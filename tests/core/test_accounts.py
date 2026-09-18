"""U01/U05–U08: HTTP-Rechte, echte CSRF-Tokens, Sitzungen und Kontoregeln."""

from concurrent.futures import ThreadPoolExecutor
import re
import time

import pytest
from sqlalchemy import select, update

from neofab2 import create_app
from neofab2.database import upgrade_database
from neofab2.core.users import create_user, edit_user, users, sessions

PASSWORD = "Synthetic password for tests!"
NEW_PASSWORD = "Another synthetic password!"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    instance = create_app({"TESTING": True, "SECRET_KEY": "a" * 64,
                           "SESSION_COOKIE_SECURE": False, "DATA_DIR": str(tmp_path / "data")})
    upgrade_database(instance)
    yield instance
    instance.extensions["neofab2_db"].dispose()


@pytest.fixture
def admin(app):
    return create_user(app, "admin@example.org", "Administration", PASSWORD, "admin", bootstrap=True)


def csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200, response.text
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)


def post(client, path, data, *, form=None):
    return client.post(path, data={**data, "csrf_token": csrf(client, form or path)})


def login(client, email="admin@example.org", password=PASSWORD):
    return post(client, "/login", {"email": email, "password": password})


def row(app, user_id):
    with app.extensions["neofab2_db"].connect() as connection:
        return connection.execute(select(users).where(users.c.id == user_id)).mappings().one()


def test_login_logout_and_cookie_replay(app, admin):
    client = app.test_client()
    response = login(client, email=" ADMIN@EXAMPLE.ORG ")
    assert response.status_code == 302
    assert response.location == "/profile"
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert "SameSite=Lax" in response.headers["Set-Cookie"]
    page = client.get("/profile")
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    assert "User management" in page.text
    assert PASSWORD not in page.text
    cookie = client.get_cookie("neofab2_session").value
    assert client.get("/logout").status_code == 405
    response = post(client, "/logout", {}, form="/profile")
    assert response.status_code == 302
    replay = app.test_client()
    replay.set_cookie("neofab2_session", cookie)
    assert replay.get("/profile").location == "/login"
    assert row(app, admin)["password_hash"].startswith("scrypt:")
    assert PASSWORD not in row(app, admin)["password_hash"]


def test_invalid_and_inactive_login_same_response(app, admin):
    client = app.test_client()
    invalid = login(client, password="wrong")
    missing = login(client, email="nobody@example.org")
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(update(users).where(users.c.id == admin).values(active=False))
    inactive = login(client)
    for response in (invalid, missing, inactive):
        assert response.status_code == 401
        assert "Unable to sign in" in response.text
        assert PASSWORD not in response.text
    assert client.get("/profile").location == "/login"


@pytest.mark.parametrize("role", ["user", "staff"])
def test_admin_routes_deny_non_admin_and_profile_cannot_escalate(app, admin, role):
    user_id = create_user(app, "person@example.org", "Person", PASSWORD, role, actor_id=admin)
    client = app.test_client()
    assert login(client, "person@example.org").status_code == 302
    assert "User management" not in client.get("/profile").text
    for path in ("/admin/users", "/admin/users/new", f"/admin/users/{admin}/edit"):
        assert client.get(path).status_code == 403
    token = csrf(client, "/profile")
    for path in ("/admin/users/new", f"/admin/users/{admin}/edit"):
        assert client.post(path, data={"csrf_token": token, "role": "admin"}).status_code == 403
    response = post(client, "/profile", {"display_name": "New Name", "role": "admin", "email": "hijack@example.org", "user_id": admin})
    assert response.status_code == 302
    assert row(app, user_id)["role"] == role
    assert row(app, user_id)["email"] == "person@example.org"
    assert row(app, admin)["display_name"] == "Administration"


def test_csrf_blocks_login_logout_and_mutation(app, admin):
    client = app.test_client()
    assert client.post("/login", data={"email": "admin@example.org", "password": PASSWORD}).status_code == 400
    login(client)
    for path in ("/logout", "/profile", "/profile/password", "/admin/users/new", f"/admin/users/{admin}/edit"):
        assert client.post(path, data={"display_name": "Changed"}).status_code == 400
    assert row(app, admin)["display_name"] == "Administration"
    assert client.get("/profile").status_code == 200


def test_admin_create_duplicate_validation_and_escaping(app, admin):
    client = app.test_client()
    login(client)
    data = {"display_name": '<script>alert("x")</script>', "email": "person@example.org",
            "role": "staff", "password": PASSWORD, "confirm_password": PASSWORD}
    assert post(client, "/admin/users/new", data).status_code == 302
    assert post(client, "/admin/users/new", {**data, "email": "PERSON@example.org"}).status_code == 400
    assert post(client, "/admin/users/new", {**data, "role": "superadmin"}).status_code == 400
    assert post(client, "/admin/users/new", {**data, "password": "short", "confirm_password": "short"}).status_code == 400
    assert post(client, "/admin/users/new", {**data, "email": "invalid"}).status_code == 400
    page = client.get("/admin/users")
    assert '<script>alert("x")</script>' not in page.text
    assert "&lt;script&gt;" in page.text
    assert "scrypt:" not in page.text and PASSWORD not in page.text


@pytest.mark.parametrize("role,active", [("staff", True), ("user", True), ("admin", False)])
def test_last_admin_guard_over_http(app, admin, role, active):
    client = app.test_client()
    login(client)
    data = {"email": "admin@example.org", "display_name": "Admin", "role": role}
    if active:
        data["active"] = "on"
    response = post(client, f"/admin/users/{admin}/edit", data)
    assert response.status_code == 400
    assert "last active administrator" in response.text
    assert row(app, admin)["active"] and row(app, admin)["role"] == "admin"


@pytest.mark.parametrize("change", ["deactivate", "role", "email"])
def test_admin_changes_revoke_target_sessions(app, admin, change):
    target = create_user(app, "person@example.org", "Person", PASSWORD, actor_id=admin)
    client = app.test_client()
    login(client, "person@example.org")
    cookie = client.get_cookie("neofab2_session").value
    edit_user(app, target, "new@example.org" if change == "email" else "person@example.org", "Person",
              "staff" if change == "role" else "user", change != "deactivate", actor_id=admin)
    replay = app.test_client()
    replay.set_cookie("neofab2_session", cookie)
    assert replay.get("/profile").location == "/login"
    if change == "deactivate":
        assert login(client, "person@example.org").status_code == 401
        edit_user(app, target, "person@example.org", "Person", "user", True, actor_id=admin)
        assert login(client, "person@example.org").status_code == 302


@pytest.mark.parametrize("field", ["last_seen", "created_at"])
def test_server_session_expiry(app, admin, field):
    client = app.test_client()
    login(client)
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(update(sessions).values({field: 0}))
    assert client.get("/profile").location == "/login"


def test_static_and_health_do_not_extend_session(app, admin):
    client = app.test_client()
    login(client)
    previous = int(time.time()) - 60
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(update(sessions).values(last_seen=previous))
    client.get("/static/core.css")
    client.get("/health/live")
    client.get("/health/ready")
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(sessions.c.last_seen)).scalar_one() == previous
    client.get("/profile")
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(sessions.c.last_seen)).scalar_one() > previous


def test_password_change_reauth_and_all_sessions_revoked(app, admin):
    one, two = app.test_client(), app.test_client()
    login(one)
    login(two)
    data = {"old_password": "wrong", "new_password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD}
    assert post(one, "/profile/password", data, form="/profile").status_code == 400
    assert post(one, "/profile/password", {**data, "old_password": PASSWORD}, form="/profile").status_code == 302
    assert two.get("/profile").location == "/login"
    assert login(one).status_code == 401
    assert login(one, password=NEW_PASSWORD).status_code == 302


def test_login_limit_shared_across_clients_and_expires(app, admin, monkeypatch):
    app.config["LOGIN_ACCOUNT_LIMIT"] = 2
    for _ in range(2):
        assert login(app.test_client(), password="wrong").status_code == 401
    assert login(app.test_client()).status_code == 401
    now = int(time.time())
    monkeypatch.setattr("neofab2.core.auth.time.time", lambda: now + 901)
    assert login(app.test_client()).status_code == 302


def test_concurrent_demotion_keeps_one_admin(app, admin):
    second = create_user(app, "second@example.org", "Second", PASSWORD, "admin", actor_id=admin)
    def demote(user_id):
        try:
            original = row(app, user_id)
            edit_user(app, user_id, original["email"], original["display_name"], "staff", True, actor_id=user_id)
            return "ok"
        except ValueError:
            return "protected"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(demote, [admin, second])) == ["ok", "protected"]
    with app.extensions["neofab2_db"].connect() as connection:
        assert len(connection.execute(select(users).where(users.c.role == "admin", users.c.active.is_(True))).all()) == 1


def test_concurrent_bootstrap_creates_only_one_admin(app):
    def bootstrap(index):
        try:
            create_user(app, f"admin{index}@example.org", "Admin", PASSWORD, "admin", bootstrap=True)
            return "ok"
        except ValueError:
            return "protected"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(bootstrap, [1, 2])) == ["ok", "protected"]


def test_secure_cookie_default_and_no_open_redirect(app, admin):
    app.config["SESSION_COOKIE_SECURE"] = True
    response = app.test_client().get("/login")
    assert "Secure" in response.headers["Set-Cookie"]
    app.config["SESSION_COOKIE_SECURE"] = False
    client = app.test_client()
    token = csrf(client, "/login")
    response = client.post("/login?next=https://example.org", data={"email": "admin@example.org", "password": PASSWORD, "csrf_token": token})
    assert response.location == "/profile"


def test_ip_limit_cannot_be_bypassed_with_forwarded_header(app, admin):
    app.config["LOGIN_IP_LIMIT"] = 2
    for index in range(2):
        assert login(app.test_client(), email=f"unknown{index}@example.org").status_code == 401
    client = app.test_client()
    token = csrf(client, "/login")
    response = client.post("/login", data={"email": "admin@example.org", "password": PASSWORD, "csrf_token": token},
                           headers={"X-Forwarded-For": "203.0.113.42"})
    assert response.status_code == 401


def test_unauthenticated_admin_request_does_not_expose_accounts(app, admin):
    response = app.test_client().get("/admin/users")
    assert response.status_code == 302 and response.location == "/login"
    assert "admin@example.org" not in response.text


@pytest.mark.parametrize("length,valid", [(7, False), (8, True), (128, True), (129, False)])
def test_password_length_boundaries(length, valid):
    from neofab2.core.users import hash_password
    from werkzeug.security import check_password_hash

    password = "x" * length
    if valid:
        assert check_password_hash(hash_password(password), password)
    else:
        with pytest.raises(ValueError, match="8 to 128"):
            hash_password(password)


def test_eight_character_password_create_login_and_change(app, admin):
    client = app.test_client()
    login(client)
    page = client.get("/admin/users/new")
    assert 'minlength="8"' in page.text and 'minlength="15"' not in page.text
    data = {"display_name": "Short Password Test", "email": "short@example.org", "role": "user",
            "password": "Test123!", "confirm_password": "Test123!"}
    assert post(client, "/admin/users/new", data).status_code == 302
    person = app.test_client()
    assert login(person, "short@example.org", "Test123!").status_code == 302
    assert 'minlength="8"' in person.get("/profile").text
    response = post(person, "/profile/password", {"old_password": "Test123!", "new_password": "Changed!", "confirm_password": "Changed!"}, form="/profile")
    assert response.status_code == 302
    assert login(person, "short@example.org", "Changed!").status_code == 302


def test_missing_cookie_explains_session_error_without_bypassing_csrf(app, admin):
    app.config["SESSION_COOKIE_SECURE"] = True
    # Simuliert den Browser, der das Secure-Cookie bei HTTP nicht zurücksendet.
    client = app.test_client(use_cookies=False)
    token = csrf(client, "/login")
    response = client.post("/login", data={"csrf_token": token, "email": "admin@example.org", "password": PASSWORD})
    assert response.status_code == 400
    assert "The form session is missing" in response.text
    assert "HTTPS" in response.text and 'href="/login"' in response.text
    assert PASSWORD not in response.text
    with app.extensions["neofab2_db"].connect() as connection:
        assert not connection.execute(select(sessions)).first()
    app.config["SESSION_COOKIE_SECURE"] = False
    assert login(app.test_client()).status_code == 302


@pytest.mark.parametrize("secure", [True, False])
@pytest.mark.parametrize("credentials", ["correct", "wrong_password", "unknown_email"])
def test_login_over_http_with_cookie_policy(app, admin, secure, credentials):
    """Echte HTTP-Anfragen: der Flask-Testclient erzwingt Secure nicht."""
    from http.cookiejar import CookieJar
    from threading import Thread
    from urllib.error import HTTPError
    from urllib.parse import urlencode
    from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler
    from werkzeug.serving import make_server

    app.config["SESSION_COOKIE_SECURE"] = secure
    server = make_server("127.0.0.1", 0, app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
        url = f"http://127.0.0.1:{server.server_port}/login"
        with opener.open(url, timeout=5) as response:
            page = response.read().decode()
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        data = urlencode({
            "csrf_token": token,
            "email": "unknown@example.org" if credentials == "unknown_email" else "admin@example.org",
            "password": "Wrong123!" if credentials == "wrong_password" else PASSWORD,
        }).encode()
        try:
            response = opener.open(url, data=data, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            body = response.read().decode()
            if secure:
                assert response.status == 400
                assert "The form session is missing" in body
            elif credentials == "correct":
                assert response.status == 200
                assert response.url.endswith("/profile")
            else:
                assert response.status == 401
                assert "credentials" in body
                assert "The form session is missing" not in body
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
