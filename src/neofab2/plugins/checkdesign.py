"""CheckDesign: read-only design gallery for staff and administrators."""

from flask import Blueprint, abort, render_template, request
from neofab2.plugin_api import Plugin

VERSION = "0.1.0"
COLOR_TOKENS = (
    "background", "text", "line", "muted", "accent", "border", "panel",
    "subtle", "link", "badge", "input-border", "notice", "error-border",
    "error-text", "error-bg",
)


def blueprint():
    bp = Blueprint("plugin_checkdesign", __name__, template_folder="templates",
                   static_folder="static/checkdesign", static_url_path="/assets")

    @bp.get("/")
    def index():
        theme = request.args.get("theme")
        if theme is not None and theme not in {"light", "dark"}:
            abort(400)
        # Explicit render context overrides presentation context only for this page.
        preview = {"theme": theme} if theme else {}
        return render_template("checkdesign/index.html", plugin_version=VERSION,
                               color_tokens=COLOR_TOKENS, **preview)

    return bp


plugin = Plugin(
    plugin_id="checkdesign", name="CheckDesign", version=VERSION, api_version=1,
    permission="checkdesign.access", roles=("staff", "admin"), blueprint_factory=blueprint,
)
