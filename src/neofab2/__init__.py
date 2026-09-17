"""Application Factory; Anwendungsstart führt keine Migration aus."""

from .version import __version__


def create_app(test_config=None):
    from flask import Flask

    from .config import load_config
    from .database import init_database
    from .core.routes import bp

    app = Flask(__name__)
    app.config.from_mapping(load_config(test_config))
    init_database(app)
    app.register_blueprint(bp)
    app.context_processor(lambda: {"version": __version__})

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; img-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    return app


__all__ = ["__version__", "create_app"]
