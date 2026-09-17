"""TOML-Konfiguration ohne ausführbaren Konfigurationscode."""

import os
from pathlib import Path
import tomllib


def load_config(overrides=None):
    config = {
        "DATA_DIR": str(Path.cwd() / "instance"),
        "SECRET_KEY": None,
        "TESTING": False,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": True,
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    }
    filename = os.environ.get("NEOFAB2_CONFIG")
    if filename:
        with open(filename, "rb") as stream:
            config.update(tomllib.load(stream))
    if overrides:
        config.update(overrides)
    secret = config.get("SECRET_KEY")
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("SECRET_KEY muss mindestens 32 Zeichen enthalten. Zuerst neofab2 init-config ausführen.")
    data_dir = Path(config["DATA_DIR"]).expanduser()
    if not data_dir.is_absolute():
        raise ValueError("DATA_DIR muss ein absoluter Pfad sein.")
    config["DATA_DIR"] = str(data_dir)
    return config
