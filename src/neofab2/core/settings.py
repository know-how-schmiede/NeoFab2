"""S04: ausdrücklich freigegebene öffentliche Einstellungen, keine Secrets."""

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import Column, MetaData, String, Table, Text, select
from sqlalchemy.dialects.sqlite import insert

from neofab2.database import database_ready
from .auth import permission_required
from .users import get_user, has_permission, write_transaction

settings = Table("core_settings", MetaData(),
                 Column("key", String(100), primary_key=True), Column("value", Text, nullable=False))
DEFAULTS = {
    "site_name": "NeoFab2",
    "site_tagline": "Werkstatt & Makerspace",
    "welcome_text": "Der neue Ausgangspunkt für unsere Werkstatt und unseren Makerspace.",
    "default_theme": "dark",
}
LABELS = {"site_name": "Werkstattname", "site_tagline": "Kurzbeschreibung",
          "welcome_text": "Begrüßungstext", "default_theme": "Standarddarstellung"}
LIMITS = {"site_name": 80, "site_tagline": 160, "welcome_text": 2000}
PREFIX = "core.presentation."
bp = Blueprint("settings", __name__)


def validate(values):
    if set(values) != set(DEFAULTS):
        raise ValueError("Unbekannte oder fehlende Systemeinstellung.")
    result = {}
    for key, value in values.items():
        if not isinstance(value, str):
            raise ValueError("Einstellungen müssen Text enthalten.")
        value = value.strip()
        if key == "default_theme":
            if value not in {"light", "dark"}:
                raise ValueError("Bitte eine gültige Standarddarstellung wählen.")
        elif not 1 <= len(value) <= LIMITS[key]:
            raise ValueError(f"{LABELS[key]} muss 1 bis {LIMITS[key]} Zeichen enthalten.")
        result[key] = value
    return result


def read_settings(app):
    values = dict(DEFAULTS)
    with app.extensions["neofab2_db"].connect() as connection:
        rows = connection.execute(select(settings).where(
            settings.c.key.in_([PREFIX + key for key in DEFAULTS])))
        for row in rows:
            key = row.key.removeprefix(PREFIX)
            candidate = {**values, key: row.value}
            try:
                values = validate(candidate)
            except ValueError:
                # Beschädigter Einzelwert darf keine unsichere Darstellung erzeugen.
                pass
    return values


def save_settings(app, actor_id, values):
    values = validate(values)
    with write_transaction(app) as connection:
        if not has_permission(get_user(connection, actor_id), "core.settings.manage"):
            raise PermissionError("Keine Berechtigung für Systemeinstellungen.")
        for key, value in values.items():
            statement = insert(settings).values(key=PREFIX + key, value=value)
            connection.execute(statement.on_conflict_do_update(
                index_elements=[settings.c.key], set_={"value": value}))


@bp.route("/admin/settings", methods=["GET", "POST"])
@permission_required("core.settings.manage")
def edit():
    if not database_ready(current_app):
        abort(503)
    values = read_settings(current_app)
    if request.method == "POST":
        submitted = {key: value for key, value in request.form.items() if key != "csrf_token"}
        try:
            save_settings(current_app, g.current_user["id"], submitted)
        except ValueError as error:
            return render_template("settings.html", values={**values, **{
                key: value for key, value in submitted.items() if key in DEFAULTS}}, error=str(error)), 400
        flash("Systemeinstellungen gespeichert.")
        return redirect(url_for("settings.edit"))
    return render_template("settings.html", values=values)


def register_presentation(app):
    app.register_blueprint(bp)

    @app.context_processor
    def presentation():
        # Erst bei einer HTML-Antwort lesen; Start/Health erzeugen kein Schema.
        if not hasattr(g, "site_settings"):
            g.site_settings = read_settings(app) if database_ready(app) else dict(DEFAULTS)
        user = g.get("current_user")
        theme = user["theme"] if user else "system"
        if theme not in {"light", "dark"}:
            theme = g.site_settings["default_theme"]
        return {"site_settings": g.site_settings, "theme": theme}
