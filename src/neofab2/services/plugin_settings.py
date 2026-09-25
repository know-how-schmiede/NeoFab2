"""API 1: declared, non-secret plugin settings in authenticated requests."""
import json
import re

from flask import current_app, g
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert


def validate_value(definition, value):
    if (type(value) is not type(definition.default)
            or type(value) not in (str, int, bool)
            or (type(value) is str and len(value) > 2000)
            or (type(value) is int and not -(2**63) <= value < 2**63)):
        raise ValueError("Invalid plugin setting value.")
    return value


def validate_contract(plugin, permissions):
    from neofab2.plugin_api import Setting
    if (type(plugin.settings) is not tuple or len(plugin.settings) > 32
            or (bool(plugin.settings) != (plugin.settings_permission is not None))
            or (plugin.settings_permission is not None
                and (not isinstance(plugin.settings_permission, str)
                     or plugin.settings_permission not in permissions - {plugin.permission}))):
        raise ValueError("Invalid plugin settings contract.")
    names = set()
    for definition in plugin.settings:
        if (not isinstance(definition, Setting) or not isinstance(definition.name, str)
                or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", definition.name)
                or definition.name in names
                or len(f"plugin.{plugin.plugin_id}.{definition.name}") > 100):
            raise ValueError("Invalid plugin settings contract.")
        validate_value(definition, definition.default)
        names.add(definition.name)


def validate_connection(connection):
    if connection.engine is not current_app.extensions["neofab2_db"] or not connection.in_transaction():
        raise ValueError("An active NeoFab2 transaction is required.")


def _context(connection, plugin_id, write=False):
    from neofab2.core.users import get_user
    from neofab2.services.mail import active_modules
    registry = current_app.extensions["neofab2_plugins"]
    plugin = registry.available.get(plugin_id)
    user = get_user(connection, g.current_user["id"]) if g.get("current_user") else None
    if (plugin is None or not plugin.settings or not user or user["activation_pending"]
            or plugin_id not in active_modules(current_app, connection)
            or not registry.allows(user, plugin.permission)
            or (write and not registry.allows(user, plugin.settings_permission))):
        raise PermissionError("Plugin settings permission required.")
    return plugin, user


def read_settings(plugin_id, *, connection=None):
    """Readable to plugin entrants: never store passwords or personal data here."""
    from neofab2.core.settings import settings

    def read(conn):
        plugin, _user = _context(conn, plugin_id)
        prefix = f"plugin.{plugin_id}."
        definitions = {item.name: item for item in plugin.settings}
        result = {name: item.default for name, item in definitions.items()}
        rows = conn.execute(select(settings).where(settings.c.key.in_(
            [prefix + name for name in definitions])))
        for row in rows:
            name = row.key.removeprefix(prefix)
            try:
                result[name] = validate_value(definitions[name], json.loads(row.value))
            except (ValueError, TypeError) as error:
                raise ValueError("Invalid stored plugin setting; restore a valid value.") from error
        return result

    if connection is not None:
        validate_connection(connection)
        return read(connection)
    with current_app.extensions["neofab2_db"].connect() as conn:
        return read(conn)


def save_settings(plugin_id, values, *, connection=None):
    """Atomically replace all declared values, with an audit event without values."""
    from neofab2.core.settings import settings
    from neofab2.core.users import write_transaction
    from neofab2.services.audit import _insert

    def save(conn):
        # SQLite legacy mode may have a SQLAlchemy transaction but no SQL BEGIN.
        # Start the outer transaction before SAVEPOINT so its release cannot commit.
        if not conn.connection.driver_connection.in_transaction:
            conn.exec_driver_sql("BEGIN IMMEDIATE")
        plugin, user = _context(conn, plugin_id, write=True)
        definitions = {item.name: item for item in plugin.settings}
        if type(values) is not dict or set(values) != set(definitions):
            raise ValueError("Unknown or missing plugin setting.")
        encoded = {name: json.dumps(validate_value(definitions[name], value))
                   for name, value in values.items()}
        # A savepoint also rolls back if a caller catches an audit/database error.
        with conn.begin_nested():
            for name, value in encoded.items():
                statement = insert(settings).values(key=f"plugin.{plugin_id}.{name}", value=value)
                conn.execute(statement.on_conflict_do_update(
                    index_elements=[settings.c.key], set_={"value": value}))
            _insert(conn, plugin_id, plugin.settings_permission, user["id"], None)

    if connection is not None:
        validate_connection(connection)
        return save(connection)
    with write_transaction(current_app) as conn:
        return save(conn)
