"""U05/S04: administrator-maintained choices for user attributes."""

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, select, update
from sqlalchemy.exc import IntegrityError

from neofab2.database import database_ready
from .auth import permission_required
from .users import DETAIL_FIELDS, require_actor, users, write_transaction

KINDS = {"position": "Positions", "study_program": "Study programs", "cost_center": "Cost centers"}
options = Table("core_user_options", MetaData(),
                Column("id", Integer, primary_key=True), Column("kind", String(20)),
                Column("name", String(150)), Column("active", Boolean))
bp = Blueprint("user_options", __name__)


def list_options(connection):
    result = {kind: [] for kind in KINDS}
    for row in connection.execute(select(options).order_by(options.c.name, options.c.id)).mappings():
        result[row["kind"]].append(row)
    return result


def validate_choices(connection, values, existing=None):
    """Run inside the same write transaction as the account update."""
    for kind in KINDS.keys() & values.keys():
        value = values[kind]
        if not value:
            continue
        row = connection.execute(select(options).where(
            options.c.kind == kind, options.c.name == value)).mappings().first()
        if not row or (not row["active"] and (existing is None or existing[kind] != value)):
            raise ValueError("Select an active option from the list, or leave the field empty.")


def save_option(app, actor_id, kind, name, active, option_id=None):
    if kind not in KINDS or type(active) is not bool:
        raise ValueError("Invalid option type or status.")
    limit = DETAIL_FIELDS[kind][1]
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= limit:
        raise ValueError("Enter a name within the displayed character limit.")
    name = name.strip()
    try:
        with write_transaction(app) as connection:
            require_actor(connection, actor_id)
            if option_id is None:
                connection.execute(options.insert().values(kind=kind, name=name, active=active))
            else:
                old = connection.execute(select(options).where(
                    options.c.id == option_id, options.c.kind == kind)).mappings().first()
                if not old:
                    raise ValueError("Option not found.")
                connection.execute(update(options).where(options.c.id == option_id).values(name=name, active=active))
                # Existing assignments follow a rename atomically; deactivation
                # prevents new assignments but retains existing selections.
                connection.execute(update(users).where(users.c[kind] == old["name"]).values({kind: name}))
    except IntegrityError as error:
        raise ValueError("An option with this name already exists in this list.") from error


@bp.route("/admin/user-options/<kind>", methods=["GET", "POST"])
@bp.route("/admin/user-options/<kind>/<int:option_id>/edit", methods=["GET", "POST"])
@permission_required("core.users.manage")
def manage(kind, option_id=None):
    if kind not in KINDS:
        abort(404)
    if not database_ready(current_app):
        abort(503)
    with current_app.extensions["neofab2_db"].connect() as connection:
        entries = list_options(connection)[kind]
    entry = next((row for row in entries if row["id"] == option_id), None)
    if option_id is not None and entry is None:
        abort(404)
    error = None
    if request.method == "POST":
        try:
            statuses = request.form.getlist("active")
            if set(statuses) - {"on", "off"}:
                raise ValueError("Invalid option status.")
            save_option(current_app, g.current_user["id"], kind,
                        request.form.get("name", ""), "on" in statuses, option_id)
        except ValueError as failure:
            error = str(failure)
            entry = {"name": request.form.get("name", ""), "active": "on" in request.form.getlist("active")}
        else:
            flash("Option saved.")
            return redirect(url_for("user_options.manage", kind=kind))
    return render_template("user_options.html", kinds=KINDS, kind=kind, entries=entries,
                           entry=entry or {"name": "", "active": True}, editing=option_id is not None,
                           limit=DETAIL_FIELDS[kind][1], error=error), 400 if error else 200
