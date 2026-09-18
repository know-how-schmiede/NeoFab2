"""Persistenter Plugin-Zielzustand; laufende Registrierungen bleiben unverändert."""

import json
from pathlib import Path

from sqlalchemy import inspect, select
from sqlalchemy.dialects.sqlite import insert

from neofab2.plugin_api.registry import Registry
from .settings import settings
from .users import get_user, has_permission, write_transaction

STATE_KEY = "core.plugins.enabled"


def _read(connection, fallback):
    value = connection.execute(select(settings.c.value).where(settings.c.key == STATE_KEY)).scalar_one_or_none()
    if value is None:
        return fallback, "config"
    try:
        enabled = json.loads(value)
    except (ValueError, TypeError) as error:
        raise ValueError("The saved plugin selection is invalid. Use the local recovery command.") from error
    if (not isinstance(enabled, list) or any(not isinstance(key, str) for key in enabled)
            or len(set(enabled)) != len(enabled)):
        raise ValueError("The saved plugin selection must contain unique plugin IDs.")
    return enabled, "database"


def read_selection(app):
    fallback = app.config["ENABLED_PLUGINS"]
    # Neue Installation: Lesen darf weder Datenbankdatei noch Schema erzeugen.
    if not (Path(app.config["DATA_DIR"]) / "neofab2.sqlite3").is_file():
        return fallback, "config"
    with app.extensions["neofab2_db"].connect() as connection:
        if not inspect(connection).has_table("core_settings"):
            return fallback, "config"
        return _read(connection, fallback)


def change_selection(app, actor_id, plugin_id, action):
    registry = app.extensions["neofab2_plugins"]
    if plugin_id not in registry.available or action not in {"enable", "disable"}:
        raise ValueError("Unknown plugin or invalid action.")
    with write_transaction(app) as connection:
        if not has_permission(get_user(connection, actor_id), "core.plugins.manage"):
            raise PermissionError("You do not have permission to manage plugins.")
        enabled, _source = _read(connection, app.config["ENABLED_PLUGINS"])
        # Jeweils auf dem aktuellen DB-Stand ändern, nicht auf einem alten Formular.
        selected = set(enabled)
        if action == "enable":
            selected.add(plugin_id)
        else:
            selected.discard(plugin_id)
        desired = sorted(selected)
        Registry(registry.available.values(), desired)
        statement = insert(settings).values(key=STATE_KEY, value=json.dumps(desired))
        connection.execute(statement.on_conflict_do_update(
            index_elements=[settings.c.key], set_={"value": json.dumps(desired)}))


def restore_config_selection(app):
    """Lokaler Betriebszugang: geprüfte TOML-Auswahl als neuen DB-Zielzustand setzen."""
    desired = app.config["ENABLED_PLUGINS"]
    Registry(app.extensions["neofab2_plugins"].available.values(), desired)
    with write_transaction(app) as connection:
        statement = insert(settings).values(key=STATE_KEY, value=json.dumps(desired))
        connection.execute(statement.on_conflict_do_update(
            index_elements=[settings.c.key], set_={"value": json.dumps(desired)}))
