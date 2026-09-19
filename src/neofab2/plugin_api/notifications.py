"""Additiver API-1-Vertrag: autorisierte Versandaufträge im Request."""

from flask import current_app, g


def enqueue_email(plugin_id, dedupe_key, recipient, subject, body, *, connection=None):
    """Optional caller transaction joins business changes and enqueue atomically.

    The caller must additionally enforce business-specific recipient/owner rules.
    Without a connection this function opens and commits its own transaction.
    """
    from neofab2.core.users import get_user, write_transaction
    from neofab2.services.mail import active_modules, enqueue

    def submit(conn):
        registry = current_app.extensions["neofab2_plugins"]
        plugin = registry.available.get(plugin_id)
        user = get_user(conn, g.current_user["id"]) if g.get("current_user") else None
        if (plugin is None or plugin_id not in active_modules(current_app, conn)
                or plugin.mail_permission is None or not registry.allows(user, plugin.permission)
                or not registry.allows(user, plugin.mail_permission)):
            raise PermissionError("Mail permission required.")
        return enqueue(conn, plugin_id, dedupe_key, recipient, subject, body)

    if connection is not None:
        if connection.engine is not current_app.extensions["neofab2_db"] or not connection.in_transaction():
            raise ValueError("An active NeoFab2 transaction is required.")
        return submit(connection)
    with write_transaction(current_app) as conn:
        return submit(conn)
