"""Observed application state; does not query systemd or probe external servers."""
import secrets
import time
from sqlalchemy import BigInteger, Column, MetaData, String, Table, func, select, update
from sqlalchemy.dialects.sqlite import insert

workers = Table("core_worker_status", MetaData(), Column("name", String(40), primary_key=True),
    Column("run_id", String(32)), Column("started_at", BigInteger),
    Column("finished_at", BigInteger), Column("state", String(16)))


def worker_started(app):
    from neofab2.core.users import write_transaction
    run_id = secrets.token_hex(16)
    with write_transaction(app) as conn:
        statement = insert(workers).values(name="mail", run_id=run_id,
            started_at=int(time.time()), finished_at=None, state="running")
        conn.execute(statement.on_conflict_do_update(index_elements=[workers.c.name],
            set_={key: statement.excluded[key] for key in ("run_id", "started_at", "finished_at", "state")}))
    return run_id


def worker_finished(app, run_id, failed=False):
    from neofab2.core.users import write_transaction
    with write_transaction(app) as conn:
        conn.execute(update(workers).where(workers.c.name == "mail", workers.c.run_id == run_id).values(
            finished_at=int(time.time()), state="failed" if failed else "finished"))


def snapshot(app, connection):
    from neofab2.core.plugin_state import _read
    from neofab2.plugin_api.registry import Registry
    from neofab2.services import mail
    from neofab2.version import __version__
    from alembic.migration import MigrationContext
    registry = app.extensions["neofab2_plugins"]
    selection_valid = True
    try:
        selected = set(_read(connection, app.config["ENABLED_PLUGINS"])[0])
        Registry(registry.available.values(), sorted(selected))
    except ValueError:
        selection_valid, selected = False, set()
    loaded = {p.plugin_id for p in registry.ordered}
    plugins = [dict(id=p.plugin_id, version=p.version, loaded=p.plugin_id in loaded,
                    selected=p.plugin_id in selected) for p in registry.available.values()]
    try:
        smtp = "enabled" if mail.read_settings(connection)["enabled"] else "paused"
    except ValueError:
        smtp = "invalid"
    counts = dict(connection.execute(select(mail.outbox.c.status, func.count()).group_by(mail.outbox.c.status)).all())
    worker = connection.execute(select(workers).where(workers.c.name == "mail")).mappings().first()
    state = "never"
    if worker:
        age = int(time.time()) - (worker["finished_at"] or worker["started_at"])
        state = "stale" if age > 300 else worker["state"]
    return dict(version=__version__, schema=", ".join(MigrationContext.configure(connection).get_current_heads()), smtp=smtp, counts=counts, worker=worker, worker_state=state,
                plugins=plugins, selection_valid=selection_valid, restart=selected != loaded)
