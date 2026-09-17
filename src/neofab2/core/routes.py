from flask import Blueprint, current_app, jsonify, render_template

from neofab2.database import database_ready

bp = Blueprint("core", __name__)


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
