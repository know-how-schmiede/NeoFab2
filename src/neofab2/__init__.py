"""Application Factory; Anwendungsstart führt keine Migration aus."""

from .version import __version__


def create_app(test_config=None, *, plugins=None, use_config_plugins=False):
    from flask import Flask, render_template, request
    from flask_wtf.csrf import CSRFProtect, CSRFError

    from .config import load_config
    from .database import init_database
    from .core.routes import bp
    from .core.accounts import bp as accounts_bp
    from .core.auth import register_auth
    from .core.plugins import register_plugins
    from .core.settings import register_presentation
    from .core.plugin_state import read_selection
    from .plugin_api import builtin_plugins
    from .plugin_api.registry import Registry

    app = Flask(__name__)
    app.config.from_mapping(load_config(test_config))
    init_database(app)
    try:
        selected = app.config["ENABLED_PLUGINS"] if use_config_plugins else read_selection(app)[0]
        registry = Registry(builtin_plugins() if plugins is None else plugins, selected)
    except Exception:
        app.extensions["neofab2_db"].dispose()
        raise
    register_auth(app)
    CSRFProtect(app)
    app.register_blueprint(bp)
    app.register_blueprint(accounts_bp)
    register_plugins(app, registry)
    register_presentation(app)
    app.context_processor(lambda: {"version": __version__})

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if error.description == "The CSRF session token is missing.":
            message = (
                "Die Sitzung zum Formular fehlt. Bitte Cookies für diese Website zulassen "
                "und die Anmeldung neu öffnen. Bei einem HTTP-Testzugang muss die Administration "
                "die Cookie-Einstellung prüfen; sichere Cookies benötigen HTTPS."
            )
        else:
            message = "Die Formularsitzung ist abgelaufen oder ungültig. Bitte die Anmeldung neu öffnen und erneut versuchen."
        return render_template("error.html", message=message, login_recovery=True), 400

    @app.errorhandler(PermissionError)
    def permission_error(_error):
        return render_template("error.html", message="Für diese Aktion fehlt die Berechtigung."), 403

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", message="Für diese Seite fehlt die Berechtigung."), 403

    @app.errorhandler(503)
    def unavailable(_error):
        return render_template("error.html", message="Das System ist noch nicht bereit. Bitte die Administration informieren."), 503

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; img-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        response.headers["Referrer-Policy"] = "same-origin"
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response

    return app


__all__ = ["__version__", "create_app"]
