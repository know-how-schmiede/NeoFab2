"""Synthetisches Testplugin ohne Fachfunktion; eine nicht geheime Testeinstellung."""

from flask import Blueprint, render_template, request, redirect, url_for
from neofab2.plugin_api import Plugin, Permission, Setting
from neofab2.plugin_api.settings import read_settings, save_settings


def blueprint():
    bp = Blueprint("plugin_core_test", __name__, template_folder="templates")

    @bp.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            try:
                save_settings("core_test", {"message": request.form.get("message", "")})
            except ValueError as error:
                return render_template("core_test/index.html", values={"message": request.form.get("message", "")}, error=str(error)), 400
            return redirect(url_for("plugin_core_test.index"))
        return render_template("core_test/index.html", values=read_settings("core_test"))

    return bp


def self_check():
    return "Test plugin: task completed successfully."


plugin = Plugin(
    plugin_id="core_test", name="Core test plugin", version="0.1.0",
    api_version=1, permission="core_test.access", roles=("admin",),
    blueprint_factory=blueprint, tasks=(("self_check", self_check),),
    permissions=(Permission("core_test.settings", ("admin",)),),
    settings=(Setting("message", "Synthetic test"),),
    settings_permission="core_test.settings",
    translations={
        "de": {"Test setting": "Testeinstellung", "Save test setting": "Testeinstellung speichern", "Translation supplied by this plugin.": "Übersetzung aus diesem Plugin."},
        "fr": {"Test setting": "Paramètre de test", "Save test setting": "Enregistrer le paramètre de test", "Translation supplied by this plugin.": "Traduction fournie par ce plugin."},
    },
)
