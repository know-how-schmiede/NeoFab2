"""S09: structured audit events, deliberately without free text or request data."""
import time

from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, delete, func, select

EVENTS = {
    "login.succeeded", "login.failed", "logout", "user.created", "user.updated",
    "password.changed", "password.emergency_reset", "account.activated", "account.reset",
    "settings.changed", "smtp.changed", "accounts.changed", "plugins.changed",
    "plugins.recovered", "audit.pruned", "access.denied", "user.role_changed",
    "user.enabled", "user.disabled", "password.admin_reset",
}
events = Table("core_audit_events", MetaData(),
    Column("id", Integer, primary_key=True), Column("created_at", BigInteger),
    Column("module_id", String(80)), Column("event", String(160)),
    Column("actor_id", Integer), Column("target_id", Integer), Column("count", Integer))


def record(connection, event, *, actor_id=None, target_id=None, count=None):
    if event not in EVENTS:
        raise ValueError("Unknown audit event.")
    return _insert(connection, "core", event, actor_id, target_id, count)


def _insert(connection, module_id, event, actor_id, target_id, count=None):
    for value in (actor_id, target_id, count):
        if value is not None and (type(value) is not int or value < 0 or value > 2**63 - 1):
            raise ValueError("Audit references must be non-negative integers.")
    return connection.execute(events.insert().values(created_at=int(time.time()),
        module_id=module_id, event=event, actor_id=actor_id, target_id=target_id,
        count=count)).inserted_primary_key[0]


def prune(app, days=180, *, apply=False):
    """Local operator only. Preview by default; no scheduled deletion."""
    from neofab2.core.users import write_transaction
    if type(days) is not int or not 1 <= days <= 3650:
        raise ValueError("Retention must be between 1 and 3650 days.")
    cutoff = int(time.time()) - days * 86400
    with write_transaction(app) as connection:
        condition = events.c.created_at < cutoff
        count = connection.execute(select(func.count()).select_from(events).where(condition)).scalar_one()
        if apply:
            connection.execute(delete(events).where(condition))
            record(connection, "audit.pruned", count=count)
    return cutoff, count
