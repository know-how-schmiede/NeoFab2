"""Aus einem neutralen Verzeichnis gegen das installierte Wheel ausführen."""

from pathlib import Path
import sys
import tempfile
import re

# Optionaler --target-Pfad für die lokale Prüfung ohne Änderung der Dev-Installation.
if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])

import neofab2
from neofab2.database import upgrade_database
from neofab2.core.users import create_user

assert "site-packages" in neofab2.__file__ or "wheel-installed" in neofab2.__file__, neofab2.__file__
with tempfile.TemporaryDirectory() as folder:
    app = neofab2.create_app({"SECRET_KEY": "synthetic-test-key" * 4, "DATA_DIR": folder, "SESSION_COOKIE_SECURE": False})
    try:
        upgrade_database(app)
        client = app.test_client()
        assert client.get("/").status_code == 200
        assert client.get("/health/ready").status_code == 200
        assert client.get("/static/branding/neofab2-logo.png").status_code == 200
        assert client.get("/static/core.css").status_code == 200
        assert (Path(folder) / "neofab2.sqlite3").is_file()
        create_user(app, "wheel@example.org", "Wheel Test", "Synthetic wheel password!", "admin", bootstrap=True)
        login_page = client.get("/login")
        token = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text).group(1)
        assert client.post("/login", data={"csrf_token": token, "email": "wheel@example.org", "password": "Synthetic wheel password!"}).status_code == 302
        assert client.get("/profile").status_code == 200
        assert client.get("/admin/users").status_code == 200
    finally:
        app.extensions["neofab2_db"].dispose()
print("Wheel: Migration, Templates, CSS und Logo erfolgreich geprüft.")
