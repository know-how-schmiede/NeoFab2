"""Paket 4: S01–S04/S08/U06/U07/N01, exclusively synthetic data."""
from dataclasses import replace
from datetime import datetime
from io import BytesIO
import json
import re

import pytest
from flask import render_template_string, session
from sqlalchemy import select, update
from neofab2 import create_app
from neofab2.core.site import DEFAULTS, MAX_IMPORT, decode_import, read_settings, save
from neofab2.core.settings import DEFAULTS as APPEARANCE, read_settings as read_appearance
from neofab2.core.users import create_user, edit_user, users
from neofab2.database import upgrade_database
from neofab2.plugin_api.i18n import translate
from neofab2.plugin_api.registry import Registry
from neofab2.plugins.core_test import plugin
from neofab2.services.audit import events
from neofab2.services.presentation import format_datetime


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv('NEOFAB2_CONFIG', raising=False)
    app = create_app({'TESTING': True, 'SECRET_KEY': 'synthetic-secret' * 5,
        'DATA_DIR': str(tmp_path), 'SESSION_COOKIE_SECURE': False, 'SMTP_PASSWORD': 'private-smtp-secret',
        'ENABLED_PLUGINS': ['core_test']})
    upgrade_database(app)
    create_user(app, 'admin@example.org', 'Admin', 'Synthetic123!', 'admin', bootstrap=True)
    for role in ('staff', 'user'):
        create_user(app, role + '@example.org', role, 'Synthetic123!', role, actor_id=1)
    yield app
    app.extensions['neofab2_db'].dispose()


def csrf(client, path='/admin/settings/site'):
    return re.search(r'name="csrf_token" value="([^"]+)"', client.get(path).text)[1]


def login(app, role='admin'):
    client = app.test_client()
    assert client.post('/login', data={'csrf_token': csrf(client, '/login'), 'email': role + '@example.org',
        'password': 'Synthetic123!'}).status_code == 302
    return client


def payload(**site):
    return {'format': 'neofab2-public-settings', 'version': 1, 'presentation': dict(APPEARANCE),
            'site': {**DEFAULTS, **site}}


def upload(client, data):
    raw = data if isinstance(data, bytes) else json.dumps(data).encode()
    return client.post('/admin/settings/import', data={'csrf_token': csrf(client), 'file': (BytesIO(raw), 'settings.json')})


def test_public_pages_safe_rendering_and_restart(app):
    client = app.test_client()
    for path in ('/info', '/impressum', '/datenschutz'):
        assert client.get(path).status_code == 200
        assert 'No content has been published yet.' in client.get(path).text
    text = '# Title\n\n**Bold**\n- Entry\n<script>alert(1)</script>\n[x](javascript:alert(1))\n<img src=x onerror=alert(1)>'
    save(app, 1, {**DEFAULTS, 'imprint_markdown': text, 'timezone': 'Europe/Berlin'})
    page = client.get('/impressum').text
    assert '<h1>Title</h1>' in page and '<strong>Bold</strong>' in page and '<li>Entry</li>' in page
    assert '<script>' not in page and '<img src=x' not in page and 'href="javascript:' not in page
    assert '&lt;script&gt;' in page
    assert 'Europe/Berlin' in client.get('/info').text
    restarted = create_app(dict(app.config))
    try:
        assert read_settings(restarted)['imprint_markdown'] == text
        assert '<strong>Bold</strong>' in restarted.test_client().get('/impressum').text
    finally:
        restarted.extensions['neofab2_db'].dispose()


@pytest.mark.parametrize('path', ['/admin/settings/site', '/admin/settings/export', '/admin/roles'])
def test_permissions_and_csrf(app, path):
    assert app.test_client().get(path).location == '/login'
    for role in ('staff', 'user'):
        client = login(app, role)
        assert client.get(path).status_code == 403
        assert client.post('/admin/settings/import', data={'csrf_token': csrf(client, '/profile')}).status_code == 403
    admin = login(app)
    assert admin.get(path).status_code == 200
    assert admin.post('/admin/settings/site', data=DEFAULTS).status_code == 400
    assert admin.post('/admin/settings/import', data={}).status_code == 400


def test_export_import_atomic_secret_free_and_no_broader_changes(app):
    client = login(app)
    save(app, 1, {**DEFAULTS, 'privacy_markdown': '**Synthetic**', 'timezone': 'Europe/Berlin'})
    response = client.get('/admin/settings/export')
    assert response.mimetype == 'application/json' and 'attachment;' in response.headers['Content-Disposition']
    assert 'private-smtp-secret' not in response.text and app.config['SECRET_KEY'] not in response.text
    data = response.json
    data['presentation']['site_name'] = 'Imported workshop'
    data['site']['timezone'] = 'America/New_York'
    assert upload(client, data).status_code == 302
    assert read_settings(app)['timezone'] == 'America/New_York'
    assert read_appearance(app)['site_name'] == 'Imported workshop'
    before = read_settings(app), read_appearance(app)
    data['site']['timezone'] = '../../etc/passwd'
    data['presentation']['site_name'] = 'Must not be saved'
    assert upload(client, data).status_code == 400
    assert (read_settings(app), read_appearance(app)) == before
    with app.extensions['neofab2_db'].connect() as conn:
        assert conn.execute(select(users.c.role).where(users.c.id == 1)).scalar_one() == 'admin'
        assert conn.execute(select(events.c.event).where(events.c.event == 'settings.changed')).all()


@pytest.mark.parametrize('data', [b'null', b'[]', b'{"version":1,"version":1}', b'\xff', b'{' * 2000,
    b'x' * (MAX_IMPORT + 1), json.dumps({**payload(), 'version': True}).encode(),
    json.dumps({**payload(), 'smtp_password': 'secret'}).encode(),
    json.dumps(payload(timezone='Unknown/Zone')).encode(), json.dumps(payload(info_markdown='x'*20001)).encode(),
    json.dumps({**payload(), 'presentation': []}).encode(), json.dumps(payload(privacy_markdown=42)).encode()])
def test_invalid_imports(data):
    with pytest.raises(ValueError, match='Invalid settings file'):
        decode_import(data)


def test_form_validation_and_fresh_permissions(app):
    client = login(app)
    response = client.post('/admin/settings/site', data={**DEFAULTS, 'timezone': 'NoSuchZone',
        'privacy_markdown': 'Keep input', 'csrf_token': csrf(client)})
    assert response.status_code == 400 and 'Keep input' in response.text
    assert read_settings(app) == DEFAULTS
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id == 1).values(active=False))
    with pytest.raises(PermissionError):
        save(app, 1, DEFAULTS)
    assert client.get('/admin/settings/export').location == '/login'


@pytest.mark.parametrize(('utc', 'expected'), [
    ('2026-03-29T00:30:00+00:00', '2026-03-29 01:30:00 +0100'),
    ('2026-03-29T01:30:00+00:00', '2026-03-29 03:30:00 +0200'),
    ('2026-10-25T00:30:00+00:00', '2026-10-25 02:30:00 +0200'),
    ('2026-10-25T01:30:00+00:00', '2026-10-25 02:30:00 +0100')])
def test_dst(utc, expected):
    moment = datetime.fromisoformat(utc)
    assert format_datetime(moment, 'Europe/Berlin') == expected + ' (Europe/Berlin)'
    assert format_datetime(moment.timestamp(), 'Europe/Berlin') == expected + ' (Europe/Berlin)'


def test_time_contract_and_localized_admin_pages(app):
    with pytest.raises(ValueError):
        format_datetime(datetime(2026, 1, 1))
    assert format_datetime(0) == '1970-01-01 00:00:00 +0000 (UTC)'
    save(app, 1, {**DEFAULTS, 'timezone': 'Europe/Berlin'})
    client = login(app)
    assert '(Europe/Berlin)' in client.get('/admin/audit').text
    assert 'Times are UTC' not in client.get('/admin/settings/mail').text
    for language, expected in [('de', 'Öffentliche Inhalte und Zeitzone'), ('fr', 'Contenus publics et fuseau horaire')]:
        with app.extensions['neofab2_db'].begin() as conn:
            conn.execute(update(users).where(users.c.id == 1).values(locale=language))
        assert expected in client.get('/admin/settings/site').text


def test_role_assignment_revokes_sessions_and_protects_last_admin(app):
    client = login(app, 'user')
    admin = login(app)
    assert 'core.settings.manage' in admin.get('/admin/roles').text
    edit_user(app, 3, 'user@example.org', 'User', 'staff', True, actor_id=1)
    assert client.get('/profile').location == '/login'
    assert login(app, 'user').get('/admin/roles').status_code == 403
    with pytest.raises(ValueError, match='last active administrator'):
        edit_user(app, 1, 'admin@example.org', 'Admin', 'user', True, actor_id=1)


def test_plugin_catalog_isolation_fallback_escaping_and_validation(app):
    catalog = {'de': {'Hello {name}': 'Hallo {name}'}, 'fr': {'Hello {name}': 'Bonjour {name}'}}
    translated = replace(plugin, translations=catalog)
    registry = Registry([translated], ['core_test'])
    app.extensions['neofab2_plugins'] = registry
    catalog['de']['Hello {name}'] = 'mutated'
    with app.test_request_context('/'):
        session['locale'] = 'de'
        assert translate('core_test', 'Hello {name}', name='Test') == 'Hallo Test'
        assert translate('core_test', 'Missing') == 'Missing'
        assert '&lt;script&gt;' in render_template_string('{{ plugin_translate("core_test", "Hello {name}", name=name) }}', name='<script>')
        session['locale'] = 'fr'
        assert translate('core_test', 'Hello {name}', name='Test') == 'Bonjour Test'
        session['locale'] = 'en'
        assert translate('core_test', 'Hello {name}', name='Test') == 'Hello Test'
        with pytest.raises(ValueError):
            translate('other', 'Missing')
    for bad in ({'xx': {}}, {'de': {'Hello {name}': 'Hallo {other}'}}, {'de': {'Hello': 4}}, {'de': {'Hello': '{name.__class__}'}}):
        with pytest.raises(ValueError):
            Registry([replace(plugin, translations=bad)], [])


def test_import_rolls_back_when_audit_fails(app):
    from sqlalchemy.exc import SQLAlchemyError
    before = read_settings(app), read_appearance(app)
    with app.extensions['neofab2_db'].begin() as conn:
        conn.exec_driver_sql('DROP TABLE core_audit_events')
    with pytest.raises(SQLAlchemyError):
        save(app, 1, {**DEFAULTS, 'timezone': 'Europe/Berlin'}, appearance={**APPEARANCE, 'site_name': 'Rollback'})
    assert (read_settings(app), read_appearance(app)) == before


def test_corrupt_zone_falls_back_and_start_does_not_create_schema(tmp_path, app):
    from neofab2.core.settings import settings
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(settings.insert().values(key='core.site.timezone', value='Invalid/Zone'))
    assert read_settings(app)['timezone'] == 'UTC'
    (tmp_path / 'empty').mkdir()
    empty = create_app({'TESTING': True, 'SECRET_KEY': 'synthetic-key'*8, 'DATA_DIR': str(tmp_path/'empty')})
    try:
        from sqlalchemy import inspect
        assert inspect(empty.extensions['neofab2_db']).get_table_names() == []
        assert empty.test_client().get('/info').status_code == 503
        assert inspect(empty.extensions['neofab2_db']).get_table_names() == []
    finally:
        empty.extensions['neofab2_db'].dispose()
