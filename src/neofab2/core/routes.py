from flask import Blueprint, abort, current_app, g, jsonify, redirect, render_template, url_for

from neofab2.database import database_ready
from .users import has_permission

bp = Blueprint("core", __name__)


@bp.get("/admin")
def administration():
    if not g.get("current_user"):
        return redirect(url_for("accounts.login"))
    if not any(has_permission(g.current_user, permission) for permission in (
            "core.users.manage", "core.plugins.view", "core.settings.manage")):
        abort(403)
    return render_template("administration.html")


@bp.get("/")
def index():
    ready = database_ready(current_app)
    return render_template("index.html", ready=ready), 200 if ready else 503


@bp.get("/health/live")
def live():
    return jsonify(status="ok")


@bp.get("/health/ready")
def ready():
    is_ready = database_ready(current_app)
    return jsonify(status="ok" if is_ready else "not_ready"), 200 if is_ready else 503
