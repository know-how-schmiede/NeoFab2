"""Optional Chromium check: run with Playwright installed; synthetic temp database."""
from pathlib import Path
import tempfile
from threading import Thread
import sys

from playwright.sync_api import sync_playwright
from sqlalchemy import update, select
from werkzeug.serving import make_server

from neofab2 import create_app
from neofab2.database import upgrade_database
from neofab2.core.users import create_user, users

output = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/neofab2-user-management-ui')
output.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as folder:
    app = create_app({'TESTING': True, 'SECRET_KEY': 'synthetic-browser-key' * 4,
        'DATA_DIR': folder, 'SESSION_COOKIE_SECURE': False, 'ENABLED_PLUGINS': []})
    upgrade_database(app)
    create_user(app, 'admin@example.org', 'Synthetic Admin', 'Synthetic123!', 'admin', bootstrap=True, locale='de')
    create_user(app, 'disabled@example.org', 'Synthetic Disabled', 'Synthetic123!', actor_id=1, active=False)
    from neofab2.core.user_export import export_users
    exported = export_users(app, actor_id=1)
    server = make_server('127.0.0.1', 0, app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1440, 'height': 1050})
            page.goto(base + '/login')
            page.locator('#email').fill('admin@example.org')
            page.locator('#password').fill('Synthetic123!')
            page.locator('form:has(#password) button[type=submit]').click()
            page.wait_for_url('**/profile')
            for theme in ('dark', 'light'):
                with app.extensions['neofab2_db'].begin() as conn:
                    conn.execute(update(users).where(users.c.id == 1).values(theme=theme))
                for width in (1440, 390):
                    page.set_viewport_size({'width': width, 'height': 1050})
                    page.goto(base + '/admin/users')
                    boxes = [el.bounding_box() for el in page.locator('.button-bar a, .button-bar button').all()]
                    assert len(boxes) == 3 and all(box['height'] >= 44 for box in boxes)
                    assert max(box['height'] for box in boxes) - min(box['height'] for box in boxes) <= 2
                    if width == 1440:
                        assert len({round(box['y']) for box in boxes}) == 1
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.screenshot(path=str(output / f'users-{theme}-{width}.png'), full_page=True)
            page.goto(base + '/admin/users/2/edit')
            page.get_by_role('link', name='Benutzer löschen', exact=True).click()
            assert page.get_by_text('Dieses deaktivierte Benutzerkonto endgültig löschen?').is_visible()
            page.screenshot(path=str(output / 'confirm-light-390.png'), full_page=True)
            page.get_by_role('link', name='Abbrechen', exact=True).click()
            assert page.url.endswith('/admin/users/2/edit')
            page.get_by_role('link', name='Benutzer löschen', exact=True).click()
            page.get_by_role('checkbox').check()
            page.get_by_role('button', name='Benutzer endgültig löschen', exact=True).click()
            page.wait_for_url('**/admin/users')
            with app.extensions['neofab2_db'].connect() as conn:
                assert conn.execute(select(users.c.id).where(users.c.id == 2)).first() is None
            page.goto(base + '/admin/users/import')
            upload = {'name': 'synthetic-users.json', 'mimeType': 'application/json', 'buffer': exported}
            page.locator('#import-file').set_input_files(upload)
            page.get_by_role('button', name='Import prüfen', exact=True).click()
            page.locator('#confirm-file').set_input_files(upload)
            page.locator('input[name="skip_conflicts"]').check()
            page.locator('input[name="confirm"]').check()
            page.locator('form:has(#confirm-file) button[type="submit"]').click()
            assert page.get_by_role('heading', name='Importergebnis', exact=True).is_visible()
            with app.extensions['neofab2_db'].connect() as conn:
                assert conn.execute(select(users.c.id).where(users.c.email == 'disabled@example.org')).first() is not None
            browser.close()
        print('Chromium: toolbar dark/light at 1440/390 px; cancel, confirmed deletion and mixed-conflict import passed.')
    finally:
        server.shutdown()
        thread.join()
        app.extensions['neofab2_db'].dispose()
