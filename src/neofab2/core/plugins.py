"""Core-Anbindung des öffentlichen Plugin-Vertrags."""

from flask import Blueprint, abort, current_app, g, redirect, render_template, url_for

from .auth import permission_required
from .users import has_permission

bp = Blueprint("plugins", __name__)


@bp.get("/admin/plugins")
@permission_required("core.plugins.view")
def overview():
    registry = current_app.extensions["neofab2_plugins"]
    return render_template("plugins.html", registry=registry)


def register_plugins(app, registry):
    app.extensions["neofab2_plugins"] = registry
    for plugin in registry.ordered:
        blueprint = plugin.blueprint_factory()
        if blueprint.name != f"plugin_{plugin.plugin_id}":
            raise ValueError(f"Falscher Blueprint-Namensraum: {plugin.plugin_id}")

        def guard(permission=plugin.permission):
            if not g.get("current_user"):
                return redirect(url_for("accounts.login"))
            if not has_permission(g.current_user, permission):
                abort(403)

        # Vor allen eigenen Blueprint-Hooks prüfen.
        blueprint.before_request_funcs.setdefault(None, []).insert(0, guard)
        app.register_blueprint(blueprint, url_prefix=f"/plugins/{plugin.plugin_id}")
        if f"{blueprint.name}.index" not in app.view_functions:
            raise ValueError(f"Plugin-Einstiegsseite fehlt: {plugin.plugin_id}")
    app.register_blueprint(bp)

    @app.context_processor
    def navigation():
        return {"plugin_navigation": tuple(
            plugin for plugin in registry.ordered
            if has_permission(g.get("current_user"), plugin.permission))}
