"""API 1: audit a declared plugin action; caller enforces object-level access."""
from flask import current_app, g


def record_action(plugin_id, permission, *, target_id=None, connection=None):
    from neofab2.core.users import get_user, write_transaction
    from neofab2.services.audit import _insert
    from neofab2.services.mail import active_modules

    def submit(conn):
        registry = current_app.extensions["neofab2_plugins"]
        plugin = registry.available.get(plugin_id)
        user = get_user(conn, g.current_user["id"]) if g.get("current_user") else None
        declared = {p.name for p in plugin.permissions} | {plugin.permission} if plugin else set()
        if (plugin is None or not user or user["activation_pending"]
                or plugin_id not in active_modules(current_app, conn)
                or permission not in declared or not registry.allows(user, plugin.permission)
                or not registry.allows(user, permission)):
            raise PermissionError("Plugin audit permission required.")
        return _insert(conn, plugin_id, permission, user["id"], target_id)

    if connection is not None:
        if connection.engine is not current_app.extensions["neofab2_db"] or not connection.in_transaction():
            raise ValueError("An active NeoFab2 transaction is required.")
        return submit(connection)
    with write_transaction(current_app) as conn:
        return submit(conn)
