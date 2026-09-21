"""Admin-only audit listing and operational observations."""
from flask import Blueprint, abort, current_app, render_template, request
from sqlalchemy import select
from neofab2.database import database_ready
from neofab2.services.audit import EVENTS, events
from neofab2.services.operations import snapshot
from .auth import permission_required

bp = Blueprint("operations", __name__)


@bp.get("/admin/audit")
@permission_required("core.audit.view")
def audit_page():
    if not database_ready(current_app):
        abort(503)
    event = request.args.get("event", "")
    if event and event not in EVENTS:
        abort(400)
    page = min(100000, max(1, request.args.get("page", 1, type=int)))
    statement = select(events)
    if event:
        statement = statement.where(events.c.module_id == "core", events.c.event == event)
    with current_app.extensions["neofab2_db"].connect() as conn:
        rows = conn.execute(statement.order_by(events.c.created_at.desc(), events.c.id.desc())
            .offset((page - 1) * 50).limit(51)).mappings().all()
    return render_template("audit.html", rows=rows[:50], more=len(rows) > 50,
                           page=page, event=event, event_names=sorted(EVENTS))


@bp.get("/admin/status")
@permission_required("core.status.view")
def status_page():
    if not database_ready(current_app):
        abort(503)
    with current_app.extensions["neofab2_db"].connect() as conn:
        status = snapshot(current_app, conn)
    return render_template("status.html", status=status)
