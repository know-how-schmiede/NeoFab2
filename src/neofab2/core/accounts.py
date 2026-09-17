"""Core-Zugangs-, Profil- und Benutzerverwaltungsseiten."""

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import select

from neofab2.database import database_ready
from .auth import authenticate, permission_required, revoke_session
from .users import (ROLES, PUBLIC_COLUMNS, users, get_user, create_user, edit_user,
                    update_profile, change_password)

bp = Blueprint("accounts", __name__)


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
        return render_template("login.html", error="Anmeldung nicht möglich. Zugangsdaten prüfen oder später erneut versuchen."), 401
    return render_template("login.html")


@bp.post("/logout")
def logout():
    revoke_session(current_app)
    return redirect(url_for("accounts.login"))


@bp.route("/profile", methods=["GET", "POST"])
@permission_required("core.profile")
def profile():
    if request.method == "POST":
        try:
            update_profile(current_app, g.current_user["id"], request.form.get("display_name", ""))
        except ValueError as error:
            return render_template("profile.html", roles=ROLES, error=str(error)), 400
        flash("Profil gespeichert.")
        return redirect(url_for("accounts.profile"))
    return render_template("profile.html", roles=ROLES)


@bp.post("/profile/password")
@permission_required("core.profile")
def password():
    try:
        if request.form.get("new_password") != request.form.get("confirm_password"):
            raise ValueError("Die neuen Passwörter stimmen nicht überein.")
        change_password(current_app, g.current_user["id"], request.form.get("old_password", ""), request.form.get("new_password", ""))
    except ValueError as error:
        return render_template("profile.html", roles=ROLES, error=str(error)), 400
    session.clear()
    flash("Passwort geändert. Bitte neu anmelden; alle bisherigen Sitzungen wurden beendet.")
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
                raise ValueError("Die Passwörter stimmen nicht überein.")
            create_user(current_app, request.form.get("email", ""), request.form.get("display_name", ""),
                        request.form.get("password", ""), request.form.get("role", "user"), actor_id=g.current_user["id"])
        except ValueError as error:
            return render_template("user_form.html", entry=request.form, creating=True, roles=ROLES, error=str(error)), 400
        flash("Benutzer angelegt. Das Startpasswort persönlich über einen sicheren Weg übergeben.")
        return redirect(url_for("accounts.user_list"))
    return render_template("user_form.html", entry={"role": "user"}, creating=True, roles=ROLES)


@bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@permission_required("core.users.manage")
def user_edit(user_id):
    with current_app.extensions["neofab2_db"].connect() as connection:
        entry = get_user(connection, user_id)
    if not entry:
        abort(404)
    if request.method == "POST":
        try:
            edit_user(current_app, user_id, request.form.get("email", ""), request.form.get("display_name", ""),
                      request.form.get("role", ""), request.form.get("active") == "on", actor_id=g.current_user["id"])
        except ValueError as error:
            return render_template("user_form.html", entry=entry, creating=False, roles=ROLES, error=str(error)), 400
        flash("Benutzer gespeichert. Geänderte Zugangsdaten, Rolle oder Kontostatus beenden bisherige Sitzungen.")
        return redirect(url_for("accounts.user_list"))
    return render_template("user_form.html", entry=entry, creating=False, roles=ROLES)
