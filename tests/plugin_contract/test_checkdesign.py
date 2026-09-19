"""S01/U07/N01: read-only CheckDesign, theme isolation and role-based access."""

from html.parser import HTMLParser
import re

import pytest
from sqlalchemy import select

from neofab2 import create_app
from neofab2.core.settings import settings
from neofab2.core.users import create_user, users
from neofab2.database import upgrade_database
from neofab2.plugins.checkdesign import COLOR_TOKENS, plugin

PATH = "/plugins/checkdesign/"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("NEOFAB2_CONFIG", raising=False)
    instance = create_app({"TESTING": True, "SECRET_KEY": "s" * 64, "DATA_DIR": str(tmp_path),
        "SESSION_COOKIE_SECURE": False, "ENABLED_PLUGINS": ["checkdesign"]})
    upgrade_database(instance)
    create_user(instance, "admin@example.org", "Admin", "Test123!", "admin", bootstrap=True)
    for role in ("staff", "user"):
        create_user(instance, f"{role}@example.org", role, "Test123!", role, actor_id=1)
    yield instance
    instance.extensions["neofab2_db"].dispose()


def login(app, role):
    client = app.test_client()
    token = re.search(r'name="csrf_token" value="([^"]+)"', client.get("/login").text).group(1)
    assert client.post("/login", data={"csrf_token": token, "email": f"{role}@example.org",
                                     "password": "Test123!"}).status_code == 302
    return client


def test_role_access_navigation_assets_and_metadata(app):
    assert plugin.version == "0.1.0" and plugin.roles == ("staff", "admin")
    assert plugin.dependencies == ()
    assert app.test_client().get(PATH).location == "/login"
    for role in ("staff", "admin", "user"):
        client = login(app, role)
        allowed = role != "user"
        assert (f'href="{PATH}"' in client.get("/profile").text) == allowed
        assert client.get(PATH).status_code == (200 if allowed else 403)
        assert client.get(PATH + "assets/gallery.css").status_code == (200 if allowed else 403)
    assert "CheckDesign" in login(app, "admin").get("/admin/plugins").text


def test_theme_preview_is_local_and_does_not_save(app):
    client = login(app, "staff")
    with app.extensions["neofab2_db"].connect() as connection:
        before_users = connection.execute(select(users)).all()
        before_settings = connection.execute(select(settings)).all()
    for theme in ("light", "dark"):
        page = client.get(PATH, query_string={"theme": theme})
        assert page.status_code == 200 and f'data-theme="{theme}"' in page.text
        assert f'value="{theme}" class="secondary" aria-pressed="true"' in page.text
        assert 'data-theme="dark"' in client.get("/profile").text
    assert 'data-theme="dark"' in client.get(PATH).text
    for value in ("", "system", "invalid", '"><script>alert(1)</script>'):
        assert client.get(PATH, query_string={"theme": value}).status_code == 400
    with app.extensions["neofab2_db"].connect() as connection:
        assert connection.execute(select(users)).all() == before_users
        assert connection.execute(select(settings)).all() == before_settings
    # No gallery write endpoint, including attempts with a valid CSRF token.
    token = re.search(r'name="csrf_token" value="([^"]+)"', client.get(PATH).text).group(1)
    assert client.post(PATH, data={"csrf_token": token, "theme": "light"}).status_code == 405


def test_profile_theme_remains_default_and_other_sessions_are_isolated(app):
    from sqlalchemy import update
    with app.extensions["neofab2_db"].begin() as connection:
        connection.execute(update(users).where(users.c.role == "staff").values(theme="light", locale="de"))
    staff, admin = login(app, "staff"), login(app, "admin")
    assert 'data-theme="light"' in staff.get(PATH).text
    assert 'data-theme="dark"' in staff.get(PATH + "?theme=dark").text
    assert 'data-theme="light"' in staff.get("/profile").text
    assert 'data-theme="dark"' in admin.get(PATH).text
    assert "Formularelemente" in staff.get(PATH).text


def test_activation_and_deactivation_follow_normal_plugin_lifecycle(app):
    from neofab2.core.plugin_state import change_selection
    client = login(app, "admin")
    change_selection(app, 1, "checkdesign", "disable")
    assert client.get(PATH).status_code == 200  # Existing process remains active.
    restarted = create_app(dict(app.config))
    try:
        other = login(restarted, "admin")
        assert other.get(PATH).status_code == 404
        assert other.get(PATH + "assets/gallery.css").status_code == 404
        assert f'href="{PATH}"' not in other.get("/profile").text
        change_selection(restarted, 1, "checkdesign", "enable")
        assert other.get(PATH).status_code == 404
    finally:
        restarted.extensions["neofab2_db"].dispose()
    enabled = create_app(dict(app.config))
    try:
        assert login(enabled, "staff").get(PATH).status_code == 200
    finally:
        enabled.extensions["neofab2_db"].dispose()


class GalleryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.labels = set()
        self.fields = []
        self.references = []
        self.paths = []
        self.button = None
        self.buttons = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "label":
            self.labels.add(attrs.get("for"))
        if tag in {"input", "select", "textarea"} and attrs.get("type") != "hidden":
            self.fields.append(attrs["id"])
        self.references.extend(attrs.get("aria-describedby", "").split())
        if tag == "button" or (tag == "a" and "button" in attrs.get("class", "").split()):
            self.button = {"tag": tag, "icon": False, "text": ""}
        if tag == "svg":
            assert attrs.get("aria-hidden") == "true" and attrs.get("focusable") == "false"
            if self.button is not None:
                self.button["icon"] = True
        if tag == "path":
            assert attrs.get("d")
            self.paths.append(attrs["d"])

    def handle_data(self, data):
        if self.button is not None:
            self.button["text"] += data

    def handle_endtag(self, tag):
        if self.button is not None and self.button["tag"] == tag:
            assert self.button["icon"] and self.button["text"].strip()
            self.buttons.append(self.button)
            self.button = None


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_coverage_labels_icons_and_csp(app, theme):
    client = login(app, "staff")
    page = client.get(PATH + "?theme=" + theme)
    parser = GalleryParser()
    parser.feed(page.text)
    assert len(parser.ids) == len(set(parser.ids))
    assert set(parser.fields) <= parser.labels
    assert set(parser.references) <= set(parser.ids)
    assert {"typography", "colors", "buttons", "icons", "forms", "messages", "tables", "layout"} <= set(parser.ids)
    paths = app.jinja_env.get_template("ui_icons.html").module.icon_paths
    assert set(paths.values()) <= set(parser.paths)
    css = client.get(PATH + "assets/gallery.css").text
    for name in COLOR_TOKENS:
        assert f"design-swatch-{name}" in page.text and f"var(--{name})" in css
    assert "<script" not in page.text and 'style="' not in page.text
    assert "style-src 'self'" in page.headers["Content-Security-Policy"]
    assert page.headers["Cache-Control"] == "no-store"
