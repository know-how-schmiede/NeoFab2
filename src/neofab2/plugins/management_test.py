"""Zweites synthetisches Plugin für Abhängigkeiten und Verwaltungsprüfungen."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from neofab2.plugin_api import Dependency, FilePolicy, Permission, Plugin, permission_required
from neofab2.plugin_api.files import download_file, list_files, store_file


def blueprint():
    bp = Blueprint("plugin_management_test", __name__, template_folder="templates")

    @bp.get("/")
    def index():
        return render_template("management_test/index.html", entries=list_files("management_test"))

    @bp.post("/check")
    @permission_required("management_test.check")
    def check():
        flash("Management test successful: protected form submitted.")
        return redirect(url_for("plugin_management_test.index"))

    @bp.post("/files")
    def upload():
        try:
            store_file("management_test", request.files.get("file"))
        except ValueError as error:
            return render_template("management_test/index.html", error=str(error),
                                   entries=list_files("management_test")), 400
        flash("Test file saved.")
        return redirect(url_for("plugin_management_test.index"))

    @bp.get("/files/<file_id>")
    def download(file_id):
        return download_file("management_test", file_id)

    return bp


def self_check():
    return "Management test plugin: task completed successfully."


plugin = Plugin(
    plugin_id="management_test", name="Management test plugin", version="0.1.0",
    api_version=1, permission="management_test.access", roles=("user", "staff", "admin"),
    blueprint_factory=blueprint, dependencies=(Dependency("core_test", "0.1.0"),),
    tasks=(("self_check", self_check),),
    permissions=(
        Permission("management_test.check", ("staff", "admin")),
        Permission("management_test.upload", ("user", "staff", "admin")),
        Permission("management_test.read_own", ("user", "staff", "admin")),
        Permission("management_test.read_all", ("staff", "admin")),
    ),
    files=FilePolicy("management_test.upload", "management_test.read_own", "management_test.read_all"),
)
