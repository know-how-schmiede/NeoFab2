"""TOML-Konfiguration ohne ausführbaren Konfigurationscode."""

import os
import re
from pathlib import Path
import tomllib
from urllib.parse import urlsplit


def load_config(overrides=None):
    config = {
        "DATA_DIR": str(Path.cwd() / "instance"),
        "SECRET_KEY": None,
        "TESTING": False,
        "SMTP_PASSWORD": "",
        "PUBLIC_BASE_URL": "",
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
        raise ValueError("SECRET_KEY must contain at least 32 characters. Run neofab2 init-config first.")
    data_dir = Path(config["DATA_DIR"]).expanduser()
    if not data_dir.is_absolute():
        raise ValueError("DATA_DIR must be an absolute path.")
    config["DATA_DIR"] = str(data_dir)
    for key in ("SESSION_IDLE_SECONDS", "SESSION_MAX_SECONDS", "LOGIN_WINDOW_SECONDS", "LOGIN_ACCOUNT_LIMIT", "LOGIN_IP_LIMIT"):
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError(f"{key} must be a positive integer.")
    if type(config["SESSION_COOKIE_SECURE"]) is not bool:
        raise ValueError("SESSION_COOKIE_SECURE must be true or false.")
    if not isinstance(config["SMTP_PASSWORD"], str):
        raise ValueError("SMTP_PASSWORD must be text.")
    origin = config["PUBLIC_BASE_URL"]
    if not isinstance(origin, str):
        raise ValueError("PUBLIC_BASE_URL must be an HTTP(S) origin without path or credentials.")
    if origin:
        try:
            parsed = urlsplit(origin)
            valid = (parsed.scheme in {"http", "https"} and parsed.hostname
                     and re.fullmatch(r"[A-Za-z0-9.:-]+", parsed.hostname)
                     and not parsed.username and not parsed.password and parsed.path in {"", "/"}
                     and not parsed.query and not parsed.fragment and all(32 < ord(c) < 127 for c in origin)
                     and not parsed.netloc.endswith(":"))
            if parsed.port is not None and parsed.port < 1:
                valid = False
        except ValueError:
            valid = False
        if not valid or (parsed.scheme == "http" and config["SESSION_COOKIE_SECURE"]):
            raise ValueError("PUBLIC_BASE_URL requires HTTPS; HTTP is allowed only with SESSION_COOKIE_SECURE=false. No path or credentials.")
        config["PUBLIC_BASE_URL"] = origin.rstrip("/")
    return config
