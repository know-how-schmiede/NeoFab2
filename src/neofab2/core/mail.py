"""SMTP-Administration und Testauftrag, nur core.settings.manage."""

import secrets
import re
from datetime import datetime, timezone

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import select

from neofab2.database import database_ready
from neofab2.services import mail
from .auth import permission_required
from .users import write_transaction

bp = Blueprint("mail", __name__)


@bp.app_template_filter("mail_time")
def mail_time(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime("%d.%m.%Y %H:%M:%S UTC")


@bp.route("/admin/settings/mail", methods=["GET", "POST"])
@permission_required("core.settings.manage")
def overview():
    if not database_ready(current_app):
        abort(503)
    error = None
    if request.method == "POST":
        try:
            action = request.form.get("action")
            if action == "save":
                fields = {"csrf_token", "action", *mail.DEFAULTS}
                if set(request.form) - fields or request.form.get("enabled", "") not in {"", "on"}:
                    raise ValueError("Unknown SMTP setting.")
                try:
                    port = int(request.form.get("port", ""))
                except ValueError:
                    raise ValueError("Please enter a port between 1 and 65535.") from None
                values = {key: request.form.get(key, "") for key in ("host", "sender", "username", "mode")}
                values.update(enabled=request.form.get("enabled") == "on", port=port)
                mail.save_settings(current_app, g.current_user["id"], values)
                flash("SMTP settings saved.")
            elif action == "test":
                if not re.fullmatch(r"[a-f0-9]{32}", request.form.get("request_key", "")):
                    raise ValueError("Please reopen the test form.")
                with write_transaction(current_app) as connection:
                    mail.require_admin(connection, g.current_user["id"])
                    mail.enqueue(connection, "core", "test:" + request.form.get("request_key", ""),
                                 request.form.get("recipient", ""), "NeoFab2 SMTP-Test",
                                 "Dies ist eine ausdrücklich angeforderte Testnachricht von NeoFab2.")
                flash("Test job saved. Sending takes place on the next worker run.")
            elif action == "retry":
                mail.retry_job(current_app, g.current_user["id"], request.form.get("job_id", ""),
                               acknowledge=request.form.get("acknowledge") == "on")
                flash("Mail job queued again.")
            else:
                raise ValueError("Unknown action.")
            return redirect(url_for("mail.overview"))
        except ValueError as exc:
            error = str(exc)
    page = min(1000000, max(1, request.args.get("page", 1, type=int)))
    with current_app.extensions["neofab2_db"].connect() as connection:
        try:
            values = mail.read_settings(connection)
        except ValueError as exc:
            values, error = dict(mail.DEFAULTS), str(exc)
        columns = [c for c in mail.outbox.c if c.name not in {"body", "subject", "dedupe_key", "lease_token"}]
        jobs = list(connection.execute(select(*columns).order_by(mail.outbox.c.created_at.desc(), mail.outbox.c.id)
                                       .offset((page - 1) * 25).limit(26)).mappings())
        active = mail.active_modules(current_app, connection)
    return render_template("mail.html", values=values, jobs=jobs[:25], more=len(jobs) > 25,
                           page=page, active_modules=active, request_key=secrets.token_hex(16),
                           password_present=bool(current_app.config["SMTP_PASSWORD"]), error=error), 400 if error else 200
