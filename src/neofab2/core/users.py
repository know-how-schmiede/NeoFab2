"""Benutzerregeln und serialisierte SQLite-Schreibtransaktionen."""

from contextlib import contextmanager
import time

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import Boolean, Column, Integer, BigInteger, MetaData, String, Table, Text, select, delete, update
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

metadata = MetaData()
users = Table("core_users", metadata,
    Column("id", Integer, primary_key=True), Column("email", String(254)),
    Column("display_name", String(100)), Column("password_hash", Text),
    Column("role", String(20)), Column("active", Boolean), Column("created_at", BigInteger))
sessions = Table("core_sessions", metadata,
    Column("token_hash", String(64), primary_key=True), Column("user_id", Integer),
    Column("created_at", BigInteger), Column("last_seen", BigInteger))
attempts = Table("core_login_attempts", metadata,
    Column("key", String(64), primary_key=True), Column("count", Integer), Column("window_start", BigInteger))

ROLES = {"user": "Benutzer", "staff": "Mitarbeiter", "admin": "Administrator"}
ROLE_PERMISSIONS = {
    "user": frozenset({"core.profile"}),
    "staff": frozenset({"core.profile"}),
    "admin": frozenset({"core.profile", "core.users.manage", "core.plugins.view"}),
}
PUBLIC_COLUMNS = [users.c.id, users.c.email, users.c.display_name, users.c.role, users.c.active, users.c.created_at]


def has_permission(user, permission):
    from flask import current_app, has_app_context

    if not user or not user["active"]:
        return False
    if permission in ROLE_PERMISSIONS.get(user["role"], ()):
        return True
    registry = current_app.extensions.get("neofab2_plugins") if has_app_context() else None
    return bool(registry and registry.allows(user, permission))


def normalize_email(value):
    try:
        return validate_email(value.strip(), check_deliverability=False).normalized.casefold()
    except EmailNotValidError as error:
        raise ValueError("Bitte eine gültige E-Mail-Adresse eingeben.") from error


def validate_name(value):
    value = value.strip()
    if not 1 <= len(value) <= 100:
        raise ValueError("Der Anzeigename muss 1 bis 100 Zeichen enthalten.")
    return value


def hash_password(value):
    if not 8 <= len(value) <= 128:
        raise ValueError("Das Passwort muss 8 bis 128 Zeichen enthalten.")
    return generate_password_hash(value, method="scrypt")


@contextmanager
def write_transaction(app):
    # Serialisiert auch Erstadmin und Letzter-Admin-Regel zwischen Workern.
    with app.extensions["neofab2_db"].connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise


def get_user(connection, user_id):
    return connection.execute(select(*PUBLIC_COLUMNS).where(users.c.id == user_id)).mappings().first()


def require_actor(connection, actor_id):
    if not has_permission(get_user(connection, actor_id), "core.users.manage"):
        raise PermissionError("Keine Berechtigung zur Benutzerverwaltung.")


def create_user(app, email, display_name, password, role="user", *, actor_id=None, bootstrap=False):
    email, display_name = normalize_email(email), validate_name(display_name)
    if role not in ROLES:
        raise ValueError("Unbekannte Rolle.")
    password_hash = hash_password(password)
    try:
        with write_transaction(app) as connection:
            if bootstrap:
                if role != "admin" or connection.execute(select(users.c.id).where(users.c.role == "admin")).first():
                    raise ValueError("Ein Administrator existiert bereits. Bei Zugangsproblemen reset-admin-password verwenden.")
            else:
                require_actor(connection, actor_id)
            result = connection.execute(users.insert().values(email=email, display_name=display_name,
                password_hash=password_hash, role=role, active=True, created_at=int(time.time())))
            return result.inserted_primary_key[0]
    except IntegrityError as error:
        raise ValueError("Diese E-Mail-Adresse wird bereits verwendet.") from error


def edit_user(app, user_id, email, display_name, role, active, *, actor_id):
    email, display_name = normalize_email(email), validate_name(display_name)
    if role not in ROLES or type(active) is not bool:
        raise ValueError("Ungültige Rolle oder ungültiger Kontostatus.")
    try:
        with write_transaction(app) as connection:
            require_actor(connection, actor_id)
            target = get_user(connection, user_id)
            if not target:
                raise ValueError("Benutzer nicht gefunden.")
            if target["active"] and target["role"] == "admin" and (not active or role != "admin"):
                other = connection.execute(select(users.c.id).where(
                    users.c.role == "admin", users.c.active.is_(True), users.c.id != user_id)).first()
                if not other:
                    raise ValueError("Der letzte aktive Administrator kann nicht deaktiviert oder herabgestuft werden.")
            connection.execute(update(users).where(users.c.id == user_id).values(
                email=email, display_name=display_name, role=role, active=active))
            if target["email"] != email or target["role"] != role or target["active"] != active:
                connection.execute(delete(sessions).where(sessions.c.user_id == user_id))
    except IntegrityError as error:
        raise ValueError("Diese E-Mail-Adresse wird bereits verwendet.") from error


def update_profile(app, user_id, display_name):
    display_name = validate_name(display_name)
    with write_transaction(app) as connection:
        user = get_user(connection, user_id)
        if not user or not user["active"]:
            raise PermissionError("Konto nicht aktiv.")
        connection.execute(update(users).where(users.c.id == user_id).values(display_name=display_name))


def change_password(app, user_id, old_password, new_password):
    new_hash = hash_password(new_password)
    with write_transaction(app) as connection:
        user = connection.execute(select(users).where(users.c.id == user_id)).mappings().first()
        if not user or not user["active"] or len(old_password) > 128 or not check_password_hash(user["password_hash"], old_password):
            raise ValueError("Das aktuelle Passwort ist nicht korrekt.")
        connection.execute(update(users).where(users.c.id == user_id).values(password_hash=new_hash))
        connection.execute(delete(sessions).where(sessions.c.user_id == user_id))


def reset_admin_password(app, user_id, password, *, reactivate=False):
    from .auth import attempt_key

    new_hash = hash_password(password)
    with write_transaction(app) as connection:
        user = get_user(connection, user_id)
        if not user or user["role"] != "admin":
            raise ValueError("Administrator nicht gefunden.")
        if not user["active"] and not reactivate:
            raise ValueError("Konto deaktiviert. Nur mit --reactivate ausdrücklich wieder aktivieren.")
        connection.execute(update(users).where(users.c.id == user_id).values(password_hash=new_hash, active=True))
        connection.execute(delete(sessions).where(sessions.c.user_id == user_id))
        connection.execute(delete(attempts).where(attempts.c.key == attempt_key(app, "account", user["email"])))
