"""Core-Zugangs-, Profil- und Benutzerverwaltungsseiten."""

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import select

from neofab2.database import database_ready
from .auth import authenticate, permission_required, revoke_session
from .i18n import current_language
from .users import (ROLES, PUBLIC_COLUMNS, users, get_user, create_user, edit_user,
                    update_profile, change_password, DETAIL_FIELDS, get_admin_user)

bp = Blueprint("accounts", __name__)


@bp.app_context_processor
def user_form_fields():
    return {"detail_fields": DETAIL_FIELDS, "detail_help": {
        "salutation": "Optional form of address, such as Dr. Maximum 50 characters.",
        "first_name": "Optional given name. Maximum 100 characters.",
        "last_name": "Optional family name. Maximum 100 characters.",
        "address": "Optional contact address. Maximum 500 characters.",
        "position": "Select the person's organizational position, or leave this field empty.",
        "study_program": "Select the person's study program, or leave this field empty if not applicable.",
        "cost_center": "Select the assigned cost center, or leave this field empty if none is assigned.",
        "note": "Internal note for administrators only. Do not enter passwords or other secrets. Maximum 2000 characters.",
    }}


def submitted_details():
    return {key: request.form[key] for key in DETAIL_FIELDS if key in request.form}


def render_user_form(**context):
    from .user_options import KINDS, list_options
    with current_app.extensions["neofab2_db"].connect() as connection:
        choices = list_options(connection)
    return render_template("user_form.html", choices=choices, choice_kinds=KINDS, **context)


def submitted_active(default):
    values = request.form.getlist("active")
    if set(values) - {"on", "off"}:
        raise ValueError("Invalid account status.")
    return "on" in values if values else default


@bp.before_request
def require_schema():
    if not database_ready(current_app):
        abort(503)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.current_user:
        return redirect(url_for("accounts.profile"))
    if request.method == "POST":
        token = authenticate(current_app, request.form.get("email", ""),
                             request.form.get("password", ""), request.remote_addr or "unknown")
        if token:
            session.clear()
            session["auth_token"] = token
            return redirect(url_for("accounts.profile"))
        return render_template("login.html", error="Unable to sign in. Check your credentials or try again later."), 401
    return render_template("login.html")


@bp.post("/logout")
def logout():
    locale = current_language()
    revoke_session(current_app)
    session["locale"] = locale
    return redirect(url_for("accounts.login"))


@bp.route("/profile", methods=["GET", "POST"])
@permission_required("core.profile")
def profile():
    if request.method == "POST":
        try:
            update_profile(current_app, g.current_user["id"], request.form.get("display_name", ""),
                           request.form.get("theme"), request.form.get("locale"))
        except ValueError as error:
            return render_template("profile.html", roles=ROLES, error=str(error)), 400
        flash("Profile saved.")
        return redirect(url_for("accounts.profile"))
    return render_template("profile.html", roles=ROLES)


@bp.post("/profile/password")
@permission_required("core.profile")
def password():
    try:
        if request.form.get("new_password") != request.form.get("confirm_password"):
            raise ValueError("The new passwords do not match.")
        change_password(current_app, g.current_user["id"], request.form.get("old_password", ""), request.form.get("new_password", ""))
    except ValueError as error:
        return render_template("profile.html", roles=ROLES, error=str(error)), 400
    locale = current_language()
    session.clear()
    session["locale"] = locale
    flash("Password changed. Please sign in again; all previous sessions have ended.")
    return redirect(url_for("accounts.login"))


@bp.get("/admin/users")
@permission_required("core.users.manage")
def user_list():
    page = request.args.get("page", 1, type=int)
    if page is None or page < 1 or page > 100000:
        abort(400)
    with current_app.extensions["neofab2_db"].connect() as connection:
        entries = connection.execute(select(*PUBLIC_COLUMNS).order_by(users.c.id).offset((page - 1) * 50).limit(51)).mappings().all()
    return render_template("users.html", entries=entries[:50], more=len(entries) > 50, page=page, roles=ROLES)


@bp.route("/admin/users/new", methods=["GET", "POST"])
@permission_required("core.users.manage")
def user_new():
    if request.method == "POST":
        try:
            if request.form.get("password") != request.form.get("confirm_password"):
                raise ValueError("The passwords do not match.")
            create_user(current_app, request.form.get("email", ""), request.form.get("display_name", ""),
                        request.form.get("password", ""), request.form.get("role", "user"), actor_id=g.current_user["id"],
                        details=submitted_details(), locale=request.form.get("locale", "en"), active=submitted_active(True))
        except ValueError as error:
            return render_user_form(entry=request.form, creating=True, roles=ROLES, error=str(error)), 400
        flash("User created. Provide the initial password personally through a secure channel.")
        return redirect(url_for("accounts.user_list"))
    return render_user_form(entry={"role": "user", "locale": "en", "active": True}, creating=True, roles=ROLES)


@bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@permission_required("core.users.manage")
def user_edit(user_id):
    with current_app.extensions["neofab2_db"].connect() as connection:
        entry = get_admin_user(connection, user_id)
    if not entry:
        abort(404)
    if request.method == "POST":
        try:
            if request.form.get("new_password", "") != request.form.get("confirm_password", ""):
                raise ValueError("The new passwords do not match.")
            edit_user(current_app, user_id, request.form.get("email", ""), request.form.get("display_name", ""),
                      request.form.get("role", ""), submitted_active(False), actor_id=g.current_user["id"],
                      details=submitted_details(), locale=request.form.get("locale"),
                      new_password=request.form.get("new_password", ""))
        except ValueError as error:
            safe_fields = set(DETAIL_FIELDS) | {"display_name", "email", "role", "locale"}
            submitted = {**entry, **{key: request.form[key] for key in safe_fields if key in request.form},
                         "active": "on" in request.form.getlist("active")}
            return render_user_form(entry=submitted, creating=False, roles=ROLES, error=str(error)), 400
        flash("User saved. Changes to credentials, role or account status end existing sessions.")
        return redirect(url_for("accounts.user_list"))
    return render_user_form(entry=entry, creating=False, roles=ROLES)
