"""U02-U04/S06: configurable self-service, single-use codes and queued mail."""

import hashlib
import hmac
import json
import re
import secrets
import time

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import Column, MetaData, Table, String, Integer, BigInteger, select, update, delete
from sqlalchemy.dialects.sqlite import insert

from neofab2.database import database_ready
from neofab2.services import mail
from .auth import DUMMY_HASH, attempt_key, permission_required, token_hash
from .i18n import current_language
from .settings import settings
from .users import users, sessions, attempts, get_user, has_permission, hash_password, normalize_email, validate_name, validate_locale, write_transaction

bp = Blueprint("account_flows", __name__)
POLICY_KEY = "core.accounts"
DEFAULT_POLICY = dict(registration_enabled=False, reset_enabled=False, allow_all_domains=False, allowed_domains=[])
TTL = {"activate": 86400, "reset": 1800}
WINDOW = 900
GENERIC = "If the address is eligible, an email will be queued. Check your inbox or try again later."
INVALID_CODE = "This code is invalid, expired or already used. Please request a new code."
tokens = Table("core_account_tokens", MetaData(),
    Column("id", String(32), primary_key=True), Column("user_id", Integer), Column("purpose", String(16)),
    Column("token_hash", String(64)), Column("fingerprint", String(64)), Column("created_at", BigInteger),
    Column("expires_at", BigInteger), Column("used_at", BigInteger))
limits = Table("core_account_limits", MetaData(), Column("key", String(64), primary_key=True),
               Column("count", Integer), Column("window_start", BigInteger))


def canonical_email(value):
    return normalize_email(mail.mailbox(value))


def validate_policy(values):
    if not isinstance(values, dict) or set(values) != set(DEFAULT_POLICY):
        raise ValueError("Invalid account settings.")
    result = dict(values)
    if any(type(result[key]) is not bool for key in ("registration_enabled", "reset_enabled", "allow_all_domains")):
        raise ValueError("Invalid account settings.")
    domains = result["allowed_domains"]
    if not isinstance(domains, list) or len(domains) > 100:
        raise ValueError("Enter at most 100 exact email domains, one per line.")
    normalized = set()
    for domain in domains:
        if not isinstance(domain, str) or not domain or any(c in domain for c in "@/\\:* "):
            raise ValueError("Enter exact email domains without wildcards or URLs.")
        normalized.add(canonical_email("check@" + domain.strip()).split("@")[1])
    result["allowed_domains"] = sorted(normalized)
    if result["registration_enabled"] and not result["allow_all_domains"] and not normalized:
        raise ValueError("Choose allowed domains or explicitly allow all domains before enabling registration.")
    return result


def read_policy(connection):
    raw = connection.execute(select(settings.c.value).where(settings.c.key == POLICY_KEY)).scalar_one_or_none()
    if raw is None:
        return {**DEFAULT_POLICY, "allowed_domains": []}
    try:
        return validate_policy(json.loads(raw))
    except (ValueError, TypeError):
        # Corruption must never enable a public account flow.
        return {**DEFAULT_POLICY, "allowed_domains": []}


def allowed(policy, email):
    return policy["allow_all_domains"] or email.split("@")[1] in policy["allowed_domains"]


def save_policy(app, actor_id, values):
    values = validate_policy(values)
    with write_transaction(app) as connection:
        if not has_permission(get_user(connection, actor_id), "core.settings.manage"):
            raise PermissionError()
        if values["registration_enabled"] or values["reset_enabled"]:
            if not app.config["PUBLIC_BASE_URL"] or not mail.read_settings(connection)["enabled"]:
                raise ValueError("Configure PUBLIC_BASE_URL and enable SMTP before enabling account emails.")
        old = read_policy(connection)
        changed_registration = any(old[key] != values[key] for key in ("registration_enabled", "allow_all_domains", "allowed_domains"))
        purposes = (["activate"] if changed_registration else []) + (["reset"] if not values["reset_enabled"] else [])
        connection.execute(update(tokens).where(tokens.c.purpose.in_(purposes), tokens.c.used_at.is_(None)).values(used_at=int(time.time())))
        statement = insert(settings).values(key=POLICY_KEY, value=json.dumps(values))
        connection.execute(statement.on_conflict_do_update(index_elements=[settings.c.key], set_={"value": statement.excluded.value}))


def consume_limit(app, connection, scope, ip, email=None):
    now = int(time.time())
    connection.execute(delete(limits).where(limits.c.window_start <= now - WINDOW))
    buckets = [(attempt_key(app, "selfservice:" + scope + ":ip", ip), 20)]
    if email is not None:
        buckets.append((attempt_key(app, "selfservice:email", email), 3))
    records = {r["key"]: r for r in connection.execute(select(limits).where(limits.c.key.in_([k for k, _ in buckets]))).mappings()}
    if any(records.get(key, {}).get("count", 0) >= maximum for key, maximum in buckets):
        return False
    for key, _maximum in buckets:
        statement = insert(limits).values(key=key, count=1, window_start=now)
        connection.execute(statement.on_conflict_do_update(index_elements=[limits.c.key], set_={"count": limits.c.count + 1}))
    return True


def fingerprint(app, user):
    state = [user[key] for key in ("id", "email", "password_hash", "role", "active", "activation_pending")]
    return hmac.new(app.config["SECRET_KEY"].encode(), json.dumps(state).encode(), hashlib.sha256).hexdigest()


def code_for(app, token_id, purpose):
    # Random selector + keyed authenticator: raw codes need not be stored in the outbox.
    digest = hmac.new(app.config["SECRET_KEY"].encode(), f"account-code:{purpose}:{token_id}".encode(), hashlib.sha256).hexdigest()
    return token_id + "." + digest


def invalidate_tokens(connection, user_id):
    connection.execute(update(tokens).where(tokens.c.user_id == user_id, tokens.c.used_at.is_(None)).values(used_at=int(time.time())))


def queue_code(app, connection, user, purpose):
    now = int(time.time())
    recent = connection.execute(select(tokens.c.id).where(tokens.c.user_id == user["id"],
        tokens.c.purpose == purpose, tokens.c.created_at > now - 60)).first()
    if recent:
        return
    connection.execute(update(tokens).where(tokens.c.user_id == user["id"], tokens.c.purpose == purpose,
        tokens.c.used_at.is_(None)).values(used_at=now))
    token_id = secrets.token_hex(16)
    connection.execute(tokens.insert().values(id=token_id, user_id=user["id"], purpose=purpose,
        token_hash=token_hash(code_for(app, token_id, purpose)), fingerprint=fingerprint(app, user),
        created_at=now, expires_at=now + TTL[purpose]))
    job_id = mail.enqueue(connection, "core", "account:" + token_id, user["email"],
                          "NeoFab2 account email", "The account message is prepared by the worker.")
    connection.execute(update(mail.outbox).where(mail.outbox.c.id == job_id).values(
        account_user_id=user["id"], account_token_id=token_id))


def request_email(app, purpose, email, ip, *, display_name="", locale="en"):
    """No account existence/status result is returned to the public caller."""
    email = canonical_email(email)
    if purpose == "register":
        display_name, locale = validate_name(display_name), validate_locale(locale)
    elif purpose not in {"activate", "reset"}:
        raise ValueError("Invalid account action.")
    with write_transaction(app) as connection:
        policy = read_policy(connection)
        enabled = policy["reset_enabled"] if purpose == "reset" else policy["registration_enabled"]
        if not enabled or not app.config["PUBLIC_BASE_URL"]:
            raise ValueError("This account service is currently disabled. Contact the administration.")
        if not consume_limit(app, connection, "request", ip, email):
            return
        if purpose != "reset" and not allowed(policy, email):
            return
        user = connection.execute(select(users).where(users.c.email == email)).mappings().first()
        if purpose == "register":
            if user:
                return
            result = connection.execute(users.insert().values(email=email, display_name=display_name,
                password_hash=DUMMY_HASH, role="user", active=False, activation_pending=True,
                created_at=int(time.time()), locale=locale))
            user = connection.execute(select(users).where(users.c.id == result.inserted_primary_key[0])).mappings().one()
            queue_code(app, connection, user, "activate")
        elif user and ((purpose == "activate" and user["activation_pending"] and not user["active"])
                       or (purpose == "reset" and user["active"] and not user["activation_pending"])):
            queue_code(app, connection, user, purpose)


def eligible(app, connection, token, user):
    if (not token or not user or token["used_at"] is not None or token["expires_at"] <= int(time.time())
            or not hmac.compare_digest(token["fingerprint"], fingerprint(app, user))):
        return False
    policy = read_policy(connection)
    if token["purpose"] == "activate":
        return bool(policy["registration_enabled"] and allowed(policy, user["email"])
                    and user["activation_pending"] and not user["active"] and user["role"] == "user")
    return bool(policy["reset_enabled"] and user["active"] and not user["activation_pending"])


EMAILS = {
    "en": {
        "activate": ("Activate your NeoFab2 account", "Open {url} and paste this activation code:\n\n{code}\n\nValid for 24 hours from the request. Set your password on that page. If you did not request an account, ignore this message."),
        "reset": ("Reset your NeoFab2 password", "Open {url} and paste this reset code:\n\n{code}\n\nValid for 30 minutes from the request. If you did not request a reset, ignore this message; your password has not changed."),
        "welcome": ("Welcome to NeoFab2", "Your account is active. You can now sign in at {url}."),
        "changed": ("Your NeoFab2 password was changed", "Your password was reset and all previous sessions ended. If this was not you, contact the administration immediately. Sign in: {url}"),
    },
    "de": {
        "activate": ("NeoFab2-Konto aktivieren", "Öffnen Sie {url} und fügen Sie diesen Aktivierungscode ein:\n\n{code}\n\nGültig für 24 Stunden ab Anforderung. Legen Sie auf der Seite Ihr Passwort fest. Wenn Sie kein Konto angefordert haben, ignorieren Sie diese Nachricht."),
        "reset": ("NeoFab2-Passwort zurücksetzen", "Öffnen Sie {url} und fügen Sie diesen Rücksetzcode ein:\n\n{code}\n\nGültig für 30 Minuten ab Anforderung. Wenn Sie dies nicht angefordert haben, ignorieren Sie diese Nachricht; Ihr Passwort wurde nicht geändert."),
        "welcome": ("Willkommen bei NeoFab2", "Ihr Konto ist aktiviert. Sie können sich unter {url} anmelden."),
        "changed": ("Ihr NeoFab2-Passwort wurde geändert", "Ihr Passwort wurde zurückgesetzt und alle bisherigen Sitzungen beendet. Falls Sie dies nicht veranlasst haben, kontaktieren Sie sofort die Administration. Anmeldung: {url}"),
    },
    "fr": {
        "activate": ("Activez votre compte NeoFab2", "Ouvrez {url} et collez ce code d’activation :\n\n{code}\n\nValable 24 heures après la demande. Définissez votre mot de passe sur cette page. Si vous n’avez pas demandé de compte, ignorez ce message."),
        "reset": ("Réinitialisez votre mot de passe NeoFab2", "Ouvrez {url} et collez ce code :\n\n{code}\n\nValable 30 minutes après la demande. Si vous n’avez pas fait cette demande, ignorez ce message ; votre mot de passe n’a pas changé."),
        "welcome": ("Bienvenue sur NeoFab2", "Votre compte est actif. Connectez-vous sur {url}."),
        "changed": ("Votre mot de passe NeoFab2 a été modifié", "Votre mot de passe a été réinitialisé et toutes les sessions précédentes ont été fermées. Si vous n’êtes pas à l’origine de cette action, contactez immédiatement l’administration. Connexion : {url}"),
    },
}


def queue_notice(app, connection, user, event, key):
    subject, body = EMAILS.get(user["locale"], EMAILS["en"])[event]
    job_id = mail.enqueue(connection, "core", f"account:{event}:{key}", user["email"], subject,
                          body.format(url=app.config["PUBLIC_BASE_URL"] + "/login"))
    connection.execute(update(mail.outbox).where(mail.outbox.c.id == job_id).values(account_user_id=user["id"]))


def redeem(app, purpose, code, password, ip):
    if purpose not in TTL:
        raise ValueError(INVALID_CODE)
    with write_transaction(app) as connection:
        permitted = consume_limit(app, connection, "redeem", ip)
    if not permitted or not isinstance(code, str) or not re.fullmatch(r"[a-f0-9]{32}\.[a-f0-9]{64}", code.strip()):
        raise ValueError(INVALID_CODE)
    code = code.strip()
    # Same bounded password work before looking up a code; no token is reflected.
    new_hash = hash_password(password)
    with write_transaction(app) as connection:
        token = connection.execute(select(tokens).where(tokens.c.token_hash == token_hash(code), tokens.c.purpose == purpose)).mappings().first()
        user = connection.execute(select(users).where(users.c.id == token["user_id"])).mappings().first() if token else None
        if not eligible(app, connection, token, user):
            raise ValueError(INVALID_CODE)
        connection.execute(update(users).where(users.c.id == user["id"]).values(
            password_hash=new_hash, active=True, activation_pending=False))
        invalidate_tokens(connection, user["id"])
        connection.execute(delete(sessions).where(sessions.c.user_id == user["id"]))
        connection.execute(delete(attempts).where(attempts.c.key == attempt_key(app, "account", user["email"])))
        queue_notice(app, connection, user, "welcome" if purpose == "activate" else "changed", token["id"])


def prepare_account_mail(app, job):
    """Worker hook: account state and expiry checked before constructing the code."""
    with app.extensions["neofab2_db"].connect() as connection:
        user = connection.execute(select(users).where(users.c.id == job["account_user_id"])).mappings().first()
        if not user or not app.config["PUBLIC_BASE_URL"]:
            return None
        try:
            recipient = mail.mailbox(user["email"])
        except ValueError:
            return None
        if recipient != job["recipient"]:
            return None
        if job["account_token_id"] is None:
            return job if user["active"] and not user["activation_pending"] else None
        token = connection.execute(select(tokens).where(tokens.c.id == job["account_token_id"], tokens.c.user_id == user["id"])).mappings().first()
        if not eligible(app, connection, token, user):
            return None
        code = code_for(app, token["id"], token["purpose"])
        if not hmac.compare_digest(token_hash(code), token["token_hash"]):
            return None
        subject, body = EMAILS.get(user["locale"], EMAILS["en"])[token["purpose"]]
        path = "/activate" if token["purpose"] == "activate" else "/reset-password"
        return {**job, "subject": subject, "body": body.format(url=app.config["PUBLIC_BASE_URL"] + path, code=code)}


@bp.before_request
def require_schema():
    if not database_ready(current_app):
        abort(503)


@bp.route("/admin/settings/accounts", methods=["GET", "POST"])
@permission_required("core.settings.manage")
def settings_page():
    error = None
    if request.method == "POST":
        try:
            if set(request.form) - {"csrf_token", *DEFAULT_POLICY}:
                raise ValueError("Invalid account settings.")
            if any(request.form.get(key, "") not in {"", "on"} for key in ("registration_enabled", "reset_enabled", "allow_all_domains")):
                raise ValueError("Invalid account settings.")
            values = {key: request.form.get(key) == "on" for key in ("registration_enabled", "reset_enabled", "allow_all_domains")}
            values["allowed_domains"] = [value.strip() for value in request.form.get("allowed_domains", "").splitlines() if value.strip()]
            save_policy(current_app, g.current_user["id"], values)
            flash("Account settings saved.")
            return redirect(url_for("account_flows.settings_page"))
        except ValueError as exc:
            error = str(exc)
    with current_app.extensions["neofab2_db"].connect() as connection:
        values = read_policy(connection)
    return render_template("account_settings.html", values=values, public_url=current_app.config["PUBLIC_BASE_URL"], error=error), 400 if error else 200


@bp.route("/register", methods=["GET", "POST"], defaults={"purpose": "register"})
@bp.route("/activation-request", methods=["GET", "POST"], defaults={"purpose": "activate"})
@bp.route("/forgot-password", methods=["GET", "POST"], defaults={"purpose": "reset"})
def request_page(purpose):
    with current_app.extensions["neofab2_db"].connect() as connection:
        policy = read_policy(connection)
    if not policy["reset_enabled" if purpose == "reset" else "registration_enabled"]:
        return render_template("error.html", message="This account service is currently disabled. Contact the administration."), 403
    if request.method == "POST":
        try:
            request_email(current_app, purpose, request.form.get("email", ""), request.remote_addr or "unknown",
                          display_name=request.form.get("display_name", ""), locale=current_language())
        except ValueError as exc:
            return render_template("account_request.html", purpose=purpose, error=str(exc)), 400
        flash(GENERIC)
        return redirect(url_for("account_flows.request_page", purpose=purpose))
    return render_template("account_request.html", purpose=purpose)


@bp.route("/activate", methods=["GET", "POST"], defaults={"purpose": "activate"})
@bp.route("/reset-password", methods=["GET", "POST"], defaults={"purpose": "reset"})
def redeem_page(purpose):
    if request.method == "POST":
        try:
            if request.form.get("new_password", "") != request.form.get("confirm_password", ""):
                raise ValueError("The new passwords do not match.")
            redeem(current_app, purpose, request.form.get("code", ""), request.form.get("new_password", ""), request.remote_addr or "unknown")
        except ValueError as exc:
            return render_template("account_redeem.html", purpose=purpose, error=str(exc)), 400
        locale = current_language()
        session.clear()
        session["locale"] = locale
        flash("Your password is set. Please sign in; all previous sessions have ended.")
        return redirect(url_for("accounts.login"))
    return render_template("account_redeem.html", purpose=purpose)


def register_account_flows(app):
    app.register_blueprint(bp)
    app.extensions["neofab2_account_mail"] = prepare_account_mail

    @app.context_processor
    def account_policy_context():
        if not database_ready(app):
            return {"account_policy": DEFAULT_POLICY}
        with app.extensions["neofab2_db"].connect() as connection:
            return {"account_policy": read_policy(connection)}
