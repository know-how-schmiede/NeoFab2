"""Zweites synthetisches Plugin für Abhängigkeiten und Verwaltungsprüfungen."""

from flask import Blueprint, flash, redirect, render_template, url_for
from neofab2.plugin_api import Dependency, Plugin


def blueprint():
    bp = Blueprint("plugin_management_test", __name__, template_folder="templates")

    @bp.get("/")
    def index():
        return render_template("management_test/index.html")

    @bp.post("/check")
    def check():
        flash("Verwaltungstest erfolgreich: Geschützter Formularaufruf ausgeführt.")
        return redirect(url_for("plugin_management_test.index"))

    return bp


def self_check():
    return "Verwaltungs-Testplugin: Aufgabe erfolgreich ausgeführt."


plugin = Plugin(
    plugin_id="management_test", name="Verwaltungs-Testplugin", version="0.1.0",
    api_version=1, permission="management_test.access", roles=("admin",),
    blueprint_factory=blueprint, dependencies=(Dependency("core_test", "0.1.0"),),
    tasks=(("self_check", self_check),),
)
