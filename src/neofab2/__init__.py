"""Application Factory; Anwendungsstart führt keine Migration aus."""

from .version import __version__


def create_app(test_config=None, *, plugins=None, use_config_plugins=False):
    from flask import Flask, render_template, request
    from flask_wtf.csrf import CSRFProtect, CSRFError

    from .config import load_config
    from .database import init_database
    from .core.routes import bp
    from .core.accounts import bp as accounts_bp
    from .core.user_options import bp as user_options_bp
    from .core.auth import register_auth
    from .core.plugins import register_plugins
    from .core.settings import register_presentation
    from .core.i18n import register_i18n
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
    app.register_blueprint(user_options_bp)
    register_plugins(app, registry)
    register_presentation(app)
    register_i18n(app)
    app.context_processor(lambda: {"version": __version__})

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if error.description == "The CSRF session token is missing.":
            message = "The form session is missing. Allow cookies for this site and reopen the sign-in page. For an HTTP test connection, the administration must check the cookie setting; secure cookies require HTTPS."
        else:
            message = "The form session has expired or is invalid. Reopen the sign-in page and try again."
        return render_template("error.html", message=message, login_recovery=True), 400

    @app.errorhandler(PermissionError)
    def permission_error(_error):
        return render_template("error.html", message="You do not have permission for this action."), 403

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", message="You do not have permission to view this page."), 403

    @app.errorhandler(503)
    def unavailable(_error):
        return render_template("error.html", message="The system is not ready yet. Please contact the administration."), 503

    @app.errorhandler(413)
    def file_too_large(_error):
        return render_template("error.html", message="The upload exceeds the allowed size. Choose a smaller file."), 413

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
