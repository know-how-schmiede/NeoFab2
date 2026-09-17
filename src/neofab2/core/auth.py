"""Anmeldung und serverseitig widerrufbare Sitzungen; Flask-WTF schützt POSTs."""

from functools import wraps
import hashlib
import hmac
import secrets
import time

from flask import abort, g, redirect, request, session, url_for
from sqlalchemy import select, delete, update, or_
from werkzeug.security import check_password_hash, generate_password_hash

from .users import users, sessions, attempts, PUBLIC_COLUMNS, has_permission, write_transaction, normalize_email

# Gleicher Passwortprüfpfad auch bei unbekannter E-Mail; nie als Zugang nutzbar.
DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32), method="scrypt")


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def attempt_key(app, scope, value):
    return hmac.new(app.config["SECRET_KEY"].encode(), f"{scope}:{value}".encode(), hashlib.sha256).hexdigest()


def authenticate(app, email, password, ip):
    now = int(time.time())
    try:
        email = normalize_email(email)
    except ValueError:
        email = email.strip().casefold()
    if len(email) > 254 or not 1 <= len(password) <= 128:
        return None
    account_key = attempt_key(app, "account", email)
    ip_key = attempt_key(app, "ip", ip)
    with write_transaction(app) as connection:
        connection.execute(delete(attempts).where(attempts.c.window_start <= now - app.config["LOGIN_WINDOW_SECONDS"]))
        buckets = {row["key"]: row for row in connection.execute(select(attempts).where(
            attempts.c.key.in_([account_key, ip_key]))).mappings()}
        if any(buckets.get(key, {}).get("count", 0) >= limit for key, limit in (
                (account_key, app.config["LOGIN_ACCOUNT_LIMIT"]), (ip_key, app.config["LOGIN_IP_LIMIT"]))):
            return None
        user = connection.execute(select(users).where(users.c.email == email)).mappings().first()
        valid = check_password_hash(user["password_hash"] if user else DUMMY_HASH, password)
        if not valid or not user or not user["active"]:
            for key in (account_key, ip_key):
                if key in buckets:
                    connection.execute(update(attempts).where(attempts.c.key == key).values(count=attempts.c.count + 1))
                else:
                    connection.execute(attempts.insert().values(key=key, count=1, window_start=now))
            return None
        connection.execute(delete(attempts).where(attempts.c.key == account_key))
        connection.execute(delete(sessions).where(or_(
            sessions.c.last_seen <= now - app.config["SESSION_IDLE_SECONDS"],
            sessions.c.created_at <= now - app.config["SESSION_MAX_SECONDS"])))
        token = secrets.token_urlsafe(32)
        connection.execute(sessions.insert().values(token_hash=token_hash(token), user_id=user["id"], created_at=now, last_seen=now))
        return token


def revoke_session(app):
    token = session.get("auth_token")
    if isinstance(token, str):
        with app.extensions["neofab2_db"].begin() as connection:
            connection.execute(delete(sessions).where(sessions.c.token_hash == token_hash(token)))
    session.clear()


def register_auth(app):
    @app.before_request
    def load_current_user():
        g.current_user = None
        if request.endpoint in {"static", "core.live", "core.ready"}:
            return
        token = session.get("auth_token")
        if not isinstance(token, str):
            return
        from neofab2.database import database_ready
        if not database_ready(app):
            abort(503)
        now = int(time.time())
        with app.extensions["neofab2_db"].begin() as connection:
            row = connection.execute(select(*PUBLIC_COLUMNS, sessions.c.last_seen,
                sessions.c.created_at.label("session_created")).select_from(
                    sessions.join(users, sessions.c.user_id == users.c.id)).where(
                        sessions.c.token_hash == token_hash(token))).mappings().first()
            if (not row or not row["active"] or now - row["last_seen"] >= app.config["SESSION_IDLE_SECONDS"]
                    or now - row["session_created"] >= app.config["SESSION_MAX_SECONDS"]):
                connection.execute(delete(sessions).where(sessions.c.token_hash == token_hash(token)))
                session.clear()
                return
            connection.execute(update(sessions).where(sessions.c.token_hash == token_hash(token)).values(last_seen=now))
            g.current_user = row

    @app.context_processor
    def auth_context():
        return {"current_user": g.get("current_user"), "has_permission": has_permission}


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.get("current_user"):
                return redirect(url_for("accounts.login"))
            if not has_permission(g.current_user, permission):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
