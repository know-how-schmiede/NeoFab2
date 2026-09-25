"""Benutzerregeln und serialisierte SQLite-Schreibtransaktionen."""

from contextlib import contextmanager
import time

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import Boolean, Column, Integer, BigInteger, MetaData, String, Table, Text, select, delete, update
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from .i18n import translate
from neofab2.services.audit import record

metadata = MetaData()
DETAIL_FIELDS = {
    "salutation": ("Salutation", 50), "first_name": ("First name", 100),
    "last_name": ("Last name", 100), "address": ("Address", 500),
    "position": ("Position", 150), "cost_center": ("Cost center", 100),
    "study_program": ("Study program", 150), "note": ("Note", 2000),
}
users = Table("core_users", metadata,
    Column("id", Integer, primary_key=True), Column("email", String(254)),
    Column("display_name", String(100)), Column("password_hash", Text),
    Column("role", String(20)), Column("active", Boolean), Column("created_at", BigInteger),
    Column("activation_pending", Boolean, server_default="0"),
    Column("theme", String(10), server_default="system"),
    Column("locale", String(2), server_default="en"),
    *(Column(key, String(limit), server_default="") for key, (_label, limit) in DETAIL_FIELDS.items()))
sessions = Table("core_sessions", metadata,
    Column("token_hash", String(64), primary_key=True), Column("user_id", Integer),
    Column("created_at", BigInteger), Column("last_seen", BigInteger))
attempts = Table("core_login_attempts", metadata,
    Column("key", String(64), primary_key=True), Column("count", Integer), Column("window_start", BigInteger))

ROLES = {"user": "User", "staff": "Staff", "admin": "Administrator"}
ROLE_PERMISSIONS = {
    "user": frozenset({"core.profile"}),
    "staff": frozenset({"core.profile"}),
    "admin": frozenset({"core.profile", "core.users.manage", "core.plugins.view", "core.plugins.manage", "core.settings.manage", "core.audit.view", "core.status.view"}),
}
PUBLIC_COLUMNS = [users.c.id, users.c.email, users.c.display_name, users.c.role, users.c.active, users.c.created_at, users.c.theme, users.c.locale, users.c.activation_pending]


def has_permission(user, permission):
    from flask import current_app, has_app_context

    if not user or not user["active"] or user.get("activation_pending", False):
        return False
    if permission in ROLE_PERMISSIONS.get(user["role"], ()):
        return True
    registry = current_app.extensions.get("neofab2_plugins") if has_app_context() else None
    return bool(registry and registry.allows(user, permission))


def normalize_email(value):
    try:
        return validate_email(value.strip(), check_deliverability=False).normalized.casefold()
    except EmailNotValidError as error:
        raise ValueError("Please enter a valid email address.") from error


def validate_name(value):
    value = value.strip()
    if not 1 <= len(value) <= 100:
        raise ValueError("The display name must contain 1 to 100 characters.")
    return value


def hash_password(value):
    if not 8 <= len(value) <= 128:
        raise ValueError("The password must contain 8 to 128 characters.")
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


def get_admin_user(connection, user_id):
    # Zusatzdaten, insbesondere Notizen, nicht in die allgemeine Auth-Sitzung laden.
    return connection.execute(select(*PUBLIC_COLUMNS, *(users.c[key] for key in DETAIL_FIELDS))
                              .where(users.c.id == user_id)).mappings().first()


def validate_details(details):
    if details is None:
        return {}
    if set(details) - set(DETAIL_FIELDS):
        raise ValueError("Unknown user attribute.")
    values = {}
    for key, value in details.items():
        label, limit = DETAIL_FIELDS[key]
        if not isinstance(value, str) or len(value.strip()) > limit:
            raise ValueError(translate("{label} must contain at most {limit} characters.",
                                       label=translate(label), limit=limit))
        values[key] = value.strip()
    return values


def validate_locale(locale):
    if locale not in {"de", "en", "fr"}:
        raise ValueError("Please select a valid language.")
    return locale


def require_actor(connection, actor_id):
    if not has_permission(get_user(connection, actor_id), "core.users.manage"):
        raise PermissionError("You do not have permission to manage users.")


def create_user(app, email, display_name, password, role="user", *, actor_id=None, bootstrap=False,
                details=None, locale="en", active=True):
    email, display_name = normalize_email(email), validate_name(display_name)
    if role not in ROLES:
        raise ValueError("Unknown role.")
    if type(active) is not bool or (bootstrap and not active):
        raise ValueError("Invalid account status.")
    extra = validate_details(details)
    locale = validate_locale(locale)
    password_hash = hash_password(password)
    try:
        with write_transaction(app) as connection:
            if bootstrap:
                if role != "admin" or connection.execute(select(users.c.id).where(users.c.role == "admin")).first():
                    raise ValueError("An administrator already exists. Use reset-admin-password if you cannot sign in.")
            else:
                require_actor(connection, actor_id)
            from .user_options import validate_choices
            validate_choices(connection, extra)
            result = connection.execute(users.insert().values(id=reserve_user_id(connection), email=email, display_name=display_name,
                password_hash=password_hash, role=role, active=active, created_at=int(time.time()),
                locale=locale, **extra))
            record(connection, "user.created", actor_id=actor_id, target_id=result.inserted_primary_key[0])
            return result.inserted_primary_key[0]
    except IntegrityError as error:
        raise ValueError("This email address is already in use.") from error


def edit_user(app, user_id, email, display_name, role, active, *, actor_id, details=None, locale=None, new_password=""):
    email, display_name = normalize_email(email), validate_name(display_name)
    if role not in ROLES or type(active) is not bool:
        raise ValueError("Invalid role or account status.")
    extra = validate_details(details)
    if locale is not None:
        extra["locale"] = validate_locale(locale)
    if new_password:
        extra["password_hash"] = hash_password(new_password)
    try:
        with write_transaction(app) as connection:
            require_actor(connection, actor_id)
            target = get_admin_user(connection, user_id)
            if not target:
                raise ValueError("User not found.")
            if target["activation_pending"] and active and not new_password:
                raise ValueError("Set an initial password when activating a pending account as administrator.")
            from .user_options import validate_choices
            validate_choices(connection, extra, target)
            if target["active"] and target["role"] == "admin" and (not active or role != "admin"):
                other = connection.execute(select(users.c.id).where(
                    users.c.role == "admin", users.c.active.is_(True), users.c.id != user_id)).first()
                if not other:
                    raise ValueError("The last active administrator cannot be disabled or demoted.")
            connection.execute(update(users).where(users.c.id == user_id).values(
                email=email, display_name=display_name, role=role, active=active, activation_pending=False, **extra))
            record(connection, "user.updated", actor_id=actor_id, target_id=user_id)
            if target["role"] != role:
                record(connection, "user.role_changed", actor_id=actor_id, target_id=user_id)
            if target["active"] != active:
                record(connection, "user.enabled" if active else "user.disabled", actor_id=actor_id, target_id=user_id)
            if new_password:
                record(connection, "password.admin_reset", actor_id=actor_id, target_id=user_id)
            if new_password or target["email"] != email or target["role"] != role or target["active"] != active or target["activation_pending"]:
                connection.execute(delete(sessions).where(sessions.c.user_id == user_id))
                from .account_flows import invalidate_tokens
                invalidate_tokens(connection, user_id)
            if new_password:
                from .auth import attempt_key
                connection.execute(delete(attempts).where(attempts.c.key.in_([
                    attempt_key(app, "account", target["email"]), attempt_key(app, "account", email)])))
    except IntegrityError as error:
        raise ValueError("This email address is already in use.") from error


def update_profile(app, user_id, display_name, theme=None, locale=None):
    display_name = validate_name(display_name)
    if theme is not None and theme not in {"system", "light", "dark"}:
        raise ValueError("Please select a valid appearance.")
    if locale is not None and locale not in {"de", "en", "fr"}:
        raise ValueError("Please select a valid language.")
    with write_transaction(app) as connection:
        user = get_user(connection, user_id)
        if not user or not user["active"]:
            raise PermissionError("Account is not active.")
        values = {"display_name": display_name}
        if theme is not None:
            values["theme"] = theme
        if locale is not None:
            values["locale"] = locale
        connection.execute(update(users).where(users.c.id == user_id).values(**values))


def change_password(app, user_id, old_password, new_password):
    new_hash = hash_password(new_password)
    with write_transaction(app) as connection:
        user = connection.execute(select(users).where(users.c.id == user_id)).mappings().first()
        if not user or not user["active"] or len(old_password) > 128 or not check_password_hash(user["password_hash"], old_password):
            raise ValueError("The current password is incorrect.")
        connection.execute(update(users).where(users.c.id == user_id).values(password_hash=new_hash))
        connection.execute(delete(sessions).where(sessions.c.user_id == user_id))
        from .account_flows import invalidate_tokens
        invalidate_tokens(connection, user_id)
        record(connection, "password.changed", actor_id=user_id, target_id=user_id)


def reset_admin_password(app, user_id, password, *, reactivate=False):
    from .auth import attempt_key

    new_hash = hash_password(password)
    with write_transaction(app) as connection:
        user = get_user(connection, user_id)
        if not user or user["role"] != "admin":
            raise ValueError("Administrator not found.")
        if not user["active"] and not reactivate:
            raise ValueError("Account disabled. Use --reactivate to explicitly reactivate it.")
        connection.execute(update(users).where(users.c.id == user_id).values(password_hash=new_hash, active=True, activation_pending=False))
        from .account_flows import invalidate_tokens
        invalidate_tokens(connection, user_id)
        connection.execute(delete(sessions).where(sessions.c.user_id == user_id))
        connection.execute(delete(attempts).where(attempts.c.key == attempt_key(app, "account", user["email"])))
        record(connection, "password.emergency_reset", target_id=user_id)


def reserve_user_id(connection):
    """Monotonic IDs also after physical deletion; caller holds write_transaction."""
    from sqlalchemy import func
    from sqlalchemy.dialects.sqlite import insert
    from .settings import settings
    key = 'core.users.id_high_water'
    maximum = connection.execute(select(func.max(users.c.id))).scalar_one() or 0
    saved = connection.execute(select(settings.c.value).where(settings.c.key == key)).scalar_one_or_none()
    if saved is not None:
        if not saved.isdecimal() or len(saved) > 19:
            raise ValueError('Invalid user ID counter.')
        maximum = max(maximum, int(saved))
    if maximum >= 2**63 - 1:
        raise ValueError('User ID limit reached.')
    allocated = maximum + 1
    statement = insert(settings).values(key=key, value=str(allocated))
    connection.execute(statement.on_conflict_do_update(index_elements=[settings.c.key], set_={'value': str(allocated)}))
    return allocated
