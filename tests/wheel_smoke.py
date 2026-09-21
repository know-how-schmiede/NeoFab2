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
    app = neofab2.create_app({"SECRET_KEY": "synthetic-test-key" * 4, "DATA_DIR": folder, "SESSION_COOKIE_SECURE": False,
                            "ENABLED_PLUGINS": ["core_test"]})
    try:
        upgrade_database(app)
        client = app.test_client()
        assert client.get("/").status_code == 200
        assert client.get("/health/ready").status_code == 200
        assert client.get("/static/branding/neofab2-logo.png").status_code == 200
        assert client.get("/static/core.css").status_code == 200
        assert (Path(folder) / "neofab2.sqlite3").is_file()
        create_user(app, "wheel@example.org", "Wheel Test", "Synthetic wheel password!", "admin", bootstrap=True,
                    details={"first_name": "Wheel", "note": "Synthetic admin note"})
        login_page = client.get("/login")
        token = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text).group(1)
        assert client.post("/login", data={"csrf_token": token, "email": "wheel@example.org", "password": "Synthetic wheel password!"}).status_code == 302
        assert client.get("/profile").status_code == 200
        assert client.get("/admin/users").status_code == 200
        assert client.get("/admin/settings/mail").status_code == 200
        assert client.get("/admin/audit").status_code == 200
        assert client.get("/admin/status").status_code == 200
        assert client.get("/admin/settings/accounts").status_code == 200
        assert client.get("/activate").status_code == 200
        assert client.get("/reset-password").status_code == 200
        assert client.get("/register").status_code == 403
        from neofab2.services.mail import run_worker
        assert sum(run_worker(app).values()) == 0
        assert "Synthetic admin note" in client.get("/admin/users/1/edit").text
        assert 'name="study_program"' in client.get("/admin/users/new").text
        for kind in ["position", "study_program", "cost_center"]:
            path = f"/admin/user-options/{kind}"
            page = client.get(path)
            assert page.status_code == 200 and "No options yet" in page.text
            token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
            assert client.post(path, data={"csrf_token": token, "name": "Synthetic option", "active": "on"}).status_code == 302
        form = client.get("/admin/users/new")
        assert '<select id="position"' in form.text and 'value="Synthetic option"' in form.text
        assert 'aria-describedby="position-help"' in form.text
        assert client.get("/admin/plugins").status_code == 200
        assert client.get("/admin/settings").status_code == 200
        from neofab2.core.settings import DEFAULTS, save_settings
        save_settings(app, 1, {**DEFAULTS, "site_name": "Wheel Test", "default_theme": "light"})
        assert 'data-theme="light"' in client.get("/").text
        assert client.get("/plugins/core_test/").status_code == 200
        assert "successfully" in app.extensions["neofab2_plugins"].run_task("core_test", "self_check")
        page = client.get("/admin/plugins")
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        assert client.post("/admin/plugins/management_test/state", data={"csrf_token": token, "action": "enable"}).status_code == 302
        assert client.post("/admin/plugins/checkdesign/state", data={"csrf_token": token, "action": "enable"}).status_code == 302
        restarted = neofab2.create_app({"SECRET_KEY": "synthetic-test-key" * 4, "DATA_DIR": folder, "SESSION_COOKIE_SECURE": False})
        try:
            second_client = restarted.test_client()
            second_client.set_cookie("neofab2_session", client.get_cookie("neofab2_session").value)
            assert second_client.get("/plugins/management_test/").status_code == 200
            for theme in ("light", "dark"):
                preview = second_client.get(f"/plugins/checkdesign/?theme={theme}")
                assert preview.status_code == 200 and f'data-theme="{theme}"' in preview.text
                assert "CheckDesign" in preview.text and "0.1.0" in preview.text
                assert '<svg class="button-icon"' in preview.text
            stylesheet = second_client.get("/plugins/checkdesign/assets/gallery.css")
            assert stylesheet.status_code == 200 and "design-swatch-background" in stylesheet.text
            assert 'data-theme="light"' in second_client.get("/profile").text
            assert "successfully" in restarted.extensions["neofab2_plugins"].run_task("management_test", "self_check")
        finally:
            restarted.extensions["neofab2_db"].dispose()
    finally:
        app.extensions["neofab2_db"].dispose()
print("Wheel: Migration, Templates, CSS und Logo erfolgreich geprüft.")
