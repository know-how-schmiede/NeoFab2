"""TOML-Konfiguration ohne ausführbaren Konfigurationscode."""

import os
from pathlib import Path
import tomllib


def load_config(overrides=None):
    config = {
        "DATA_DIR": str(Path.cwd() / "instance"),
        "SECRET_KEY": None,
        "TESTING": False,
        "ENABLED_PLUGINS": [],
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": True,
        "SESSION_COOKIE_NAME": "neofab2_session",
        "SESSION_IDLE_SECONDS": 1800,
        "SESSION_MAX_SECONDS": 43200,
        "LOGIN_WINDOW_SECONDS": 900,
        "LOGIN_ACCOUNT_LIMIT": 5,
        "LOGIN_IP_LIMIT": 30,
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
    for key in ("SESSION_IDLE_SECONDS", "SESSION_MAX_SECONDS", "LOGIN_WINDOW_SECONDS", "LOGIN_ACCOUNT_LIMIT", "LOGIN_IP_LIMIT"):
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError(f"{key} muss eine positive ganze Zahl sein.")
    if type(config["SESSION_COOKIE_SECURE"]) is not bool:
        raise ValueError("SESSION_COOKIE_SECURE muss true oder false sein.")
    return config
