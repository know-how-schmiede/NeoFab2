"""Paket 4: public contents, local time and explicit non-secret settings transfer."""
import json
import time
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from neofab2.database import database_ready
from neofab2.services.audit import record
from neofab2.services.presentation import format_datetime, render_markdown, validate_timezone
from . import settings as presentation
from .auth import permission_required
from .users import ROLES, ROLE_PERMISSIONS, get_user, has_permission, write_transaction

bp = Blueprint("site", __name__)
DEFAULTS = {"timezone": "UTC", "info_markdown": "", "imprint_markdown": "", "privacy_markdown": ""}
LABELS = {"info_markdown": "Information", "imprint_markdown": "Imprint", "privacy_markdown": "Privacy"}
PREFIX = "core.site."
MAX_IMPORT = 262144


def validate(values):
    if not isinstance(values, dict) or set(values) != set(DEFAULTS):
        raise ValueError("Unknown or missing system setting.")
    if any(not isinstance(value, str) or len(value) > 20000 for value in values.values()):
        raise ValueError("Public contents must contain at most 20000 characters per page.")
    result = {key: value.strip() for key, value in values.items()}
    validate_timezone(result["timezone"])
    return result


def read_settings(app):
    values = dict(DEFAULTS)
    with app.extensions["neofab2_db"].connect() as conn:
        for key, value in conn.execute(select(presentation.settings).where(
                presentation.settings.c.key.in_([PREFIX + key for key in DEFAULTS]))):
            try:
                values = validate({**values, key.removeprefix(PREFIX): value})
            except ValueError:
                pass
    return values


def save(app, actor_id, values, *, appearance=None):
    values = validate(values)
    appearance = presentation.validate(appearance) if appearance is not None else None
    with write_transaction(app) as conn:
        if not has_permission(get_user(conn, actor_id), "core.settings.manage"):
            raise PermissionError("You do not have permission to manage system settings.")
        entries = {PREFIX + key: value for key, value in values.items()}
        if appearance is not None:
            entries.update({presentation.PREFIX + key: value for key, value in appearance.items()})
        for key, value in entries.items():
            statement = insert(presentation.settings).values(key=key, value=value)
            conn.execute(statement.on_conflict_do_update(index_elements=[presentation.settings.c.key], set_={"value": value}))
        record(conn, "settings.changed", actor_id=actor_id)


def decode_import(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Invalid settings file.")
            result[key] = value
        return result
    try:
        if len(raw) > MAX_IMPORT:
            raise ValueError()
        data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique)
        if (not isinstance(data, dict) or set(data) != {"format", "version", "presentation", "site"}
                or data["format"] != "neofab2-public-settings" or type(data["version"]) is not int or data["version"] != 1
                or not isinstance(data["presentation"], dict)):
            raise ValueError()
        return presentation.validate(data["presentation"]), validate(data["site"])
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise ValueError("Invalid settings file.") from None


@bp.route("/admin/settings/site", methods=["GET", "POST"])
@permission_required("core.settings.manage")
def edit():
    values, error = read_settings(current_app), None
    if request.method == "POST":
        values = {key: value for key, value in request.form.items() if key != "csrf_token"}
        try:
            save(current_app, g.current_user["id"], values)
            flash("System settings saved.")
            return redirect(url_for("site.edit"))
        except ValueError as exc:
            error = str(exc)
    return render_template("site_settings.html", values=values, labels=LABELS, error=error), 400 if error else 200


@bp.get("/admin/settings/export")
@permission_required("core.settings.manage")
def export():
    data = {"format": "neofab2-public-settings", "version": 1,
            "presentation": presentation.read_settings(current_app), "site": read_settings(current_app)}
    return current_app.response_class(json.dumps(data, ensure_ascii=False, indent=2), mimetype="application/json",
        headers={"Content-Disposition": 'attachment; filename="NeoFab2_public_settings.json"'})


@bp.post("/admin/settings/import")
@permission_required("core.settings.manage")
def import_settings():
    upload = request.files.get("file")
    try:
        appearance, values = decode_import(upload.read(MAX_IMPORT + 1) if upload else b"")
        save(current_app, g.current_user["id"], values, appearance=appearance)
    except ValueError as exc:
        return render_template("site_settings.html", values=read_settings(current_app), labels=LABELS, error=str(exc)), 400
    flash("System settings saved.")
    return redirect(url_for("site.edit"))


@bp.get("/admin/roles")
@permission_required("core.users.manage")
def roles():
    registry = current_app.extensions["neofab2_plugins"]
    permissions = {role: set(rights) for role, rights in ROLE_PERMISSIONS.items()}
    for plugin in registry.ordered:
        for role in plugin.roles:
            permissions[role].add(plugin.permission)
        for right in plugin.permissions:
            for role in right.roles:
                permissions[role].add(right.name)
    return render_template("roles.html", roles=ROLES, permissions=permissions)


@bp.get("/info")
@bp.get("/impressum", defaults={"page": "imprint_markdown"})
@bp.get("/datenschutz", defaults={"page": "privacy_markdown"})
def public_page(page="info_markdown"):
    if not database_ready(current_app):
        abort(503)
    values = read_settings(current_app)
    return render_template("public_page.html", title=LABELS[page], content=render_markdown(values[page]),
                           is_info=page == "info_markdown")


def register(app):
    app.register_blueprint(bp)

    @app.context_processor
    def context():
        if not hasattr(g, "public_settings"):
            g.public_settings = read_settings(app) if database_ready(app) else dict(DEFAULTS)
        return {"display_timezone": g.public_settings["timezone"], "current_time": int(time.time())}

    @app.template_filter("local_time")
    def local_time(value):
        if not hasattr(g, "public_settings"):
            g.public_settings = read_settings(app) if database_ready(app) else dict(DEFAULTS)
        return format_datetime(value, g.public_settings["timezone"])
