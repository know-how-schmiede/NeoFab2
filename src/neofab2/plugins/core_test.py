"""Synthetisches Testplugin ohne Fachfunktion oder Datenhaltung."""

from flask import Blueprint, render_template
from neofab2.plugin_api import Plugin


def blueprint():
    bp = Blueprint("plugin_core_test", __name__, template_folder="templates")

    @bp.get("/")
    def index():
        return render_template("core_test/index.html")

    return bp


def self_check():
    return "Test plugin: task completed successfully."


plugin = Plugin(
    plugin_id="core_test", name="Core test plugin", version="0.1.0",
    api_version=1, permission="core_test.access", roles=("admin",),
    blueprint_factory=blueprint, tasks=(("self_check", self_check),),
)
