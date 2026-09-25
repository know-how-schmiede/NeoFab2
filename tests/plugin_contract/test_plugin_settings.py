"""Paket 5: synthetic plugin settings, service transactions and revocation."""
from dataclasses import replace
from io import BytesIO

import pytest
from flask import g
from sqlalchemy import select, update, create_engine
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import NotFound

from neofab2 import create_app
from neofab2.core.users import users, write_transaction
from neofab2.core.settings import settings
from neofab2.core.plugin_state import change_selection
from neofab2.plugin_api import Setting, Permission
from neofab2.plugin_api.settings import read_settings, save_settings
from neofab2.plugin_api.files import store_file, list_files
from neofab2.plugin_api.registry import Registry
from neofab2.plugins.core_test import plugin as core
from neofab2.plugins.management_test import plugin
from neofab2.services.files import files
from neofab2.services.audit import events
from test_files import app, login, token

ROOT = '/plugins/core_test/'


def test_http_settings_csrf_roles_escaping_restart(app):
    admin = login(app, 'admin')
    assert admin.post(ROOT, data={'message': 'x'}).status_code == 400
    for who in ('one', 'staff'):
        client = login(app, who)
        assert client.get(ROOT).status_code == 403
        assert client.post(ROOT, data={'message': 'x', 'csrf_token': token(client, '/profile')}).status_code == 403
    assert admin.post(ROOT, data={'csrf_token': token(admin, ROOT), 'message': '<script>x</script>'}).status_code == 302
    assert '&lt;script&gt;x&lt;/script&gt;' in admin.get(ROOT).text
    assert admin.post(ROOT, data={'csrf_token': token(admin, ROOT), 'message': 'x' * 2001}).status_code == 400
    restarted = create_app(dict(app.config))
    try:
        assert '&lt;script&gt;x&lt;/script&gt;' in login(restarted, 'admin').get(ROOT).text
    finally:
        restarted.extensions['neofab2_db'].dispose()
    with app.extensions['neofab2_db'].connect() as conn:
        audit = conn.execute(select(events).where(events.c.module_id == 'core_test')).mappings().all()
        assert len(audit) == 1 and audit[0]['event'] == 'core_test.settings'
        assert '<script>' not in str(audit)


@pytest.mark.parametrize('changes', [
    {'settings_permission': None}, {'settings_permission': 'core.users.manage'},
    {'settings_permission': 'core_test.access'}, {'settings': ()},
    {'settings': (Setting('../x', ''),)}, {'settings': (Setting('x', []),)},
    {'settings': (Setting('x', ''), Setting('x', True))},
    {'settings': (Setting('x', 'x' * 2001),)},
    {'settings': (Setting('x', 2**63),)},
])
def test_invalid_declarations(changes):
    with pytest.raises(ValueError):
        Registry([replace(core, **changes)], [])


@pytest.mark.parametrize('values', [{}, {'other': 'x'}, {'message': True}, {'message': 'x' * 2001}, []])
def test_invalid_values_are_atomic(app, values):
    with app.test_request_context():
        g.current_user = {'id': 1}
        save_settings('core_test', {'message': 'before'})
        with pytest.raises(ValueError):
            save_settings('core_test', values)
        assert read_settings('core_test') == {'message': 'before'}


def test_transaction_rollback_and_foreign_connection(app, monkeypatch):
    with app.test_request_context():
        g.current_user = {'id': 1}
        with pytest.raises(RuntimeError):
            with write_transaction(app) as conn:
                save_settings('core_test', {'message': 'transaction'}, connection=conn)
                store_file('management_test', FileStorage(stream=BytesIO(b'x'), filename='x.txt'), connection=conn)
                assert read_settings('core_test', connection=conn)['message'] == 'transaction'
                raise RuntimeError('synthetic rollback')
        assert read_settings('core_test')['message'] == 'Synthetic test'
        assert list_files('management_test') == []
        def fail(*args, **kwargs):
            raise RuntimeError('synthetic audit failure')
        monkeypatch.setattr('neofab2.services.audit._insert', fail)
        with write_transaction(app) as conn:
            with pytest.raises(RuntimeError):
                save_settings('core_test', {'message': 'never'}, connection=conn)
        assert read_settings('core_test')['message'] == 'Synthetic test'
        foreign = create_engine('sqlite://')
        try:
            with foreign.begin() as conn:
                for action in (lambda: save_settings('core_test', {'message': 'x'}, connection=conn),
                               lambda: read_settings('core_test', connection=conn),
                               lambda: store_file('management_test', None, connection=conn)):
                    with pytest.raises(ValueError, match='transaction'):
                        action()
        finally:
            foreign.dispose()


@pytest.mark.parametrize('change', [{'active': False}, {'activation_pending': True}, {'role': 'user'}])
def test_fresh_account_for_services(app, change):
    with app.test_request_context():
        g.current_user = {'id': 1, 'active': True, 'role': 'admin'}
        with app.extensions['neofab2_db'].begin() as conn:
            conn.execute(update(users).where(users.c.id == 1).values(**change))
        with pytest.raises(PermissionError):
            save_settings('core_test', {'message': 'x'})
        with pytest.raises(PermissionError):
            read_settings('core_test')
        if change != {'role': 'user'}:
            with pytest.raises(PermissionError):
                store_file('management_test', FileStorage(stream=BytesIO(b'x'), filename='x.txt'))


def test_live_pause_preserves_settings_and_files(app):
    second = create_app(dict(app.config))
    try:
        with app.test_request_context():
            g.current_user = {'id': 1}
            save_settings('core_test', {'message': 'retained'})
            store_file('management_test', FileStorage(stream=BytesIO(b'x'), filename='x.txt'))
        change_selection(app, 1, 'management_test', 'disable')
        change_selection(app, 1, 'core_test', 'disable')
        with second.test_request_context():
            g.current_user = {'id': 1}
            with pytest.raises(PermissionError):
                read_settings('core_test')
            with pytest.raises(PermissionError):
                save_settings('core_test', {'message': 'x'})
            with pytest.raises(NotFound):
                list_files('management_test')
            with pytest.raises(NotFound):
                store_file('management_test', None)
        with app.extensions['neofab2_db'].connect() as conn:
            assert conn.execute(select(files.c.id)).first()
            assert conn.execute(select(settings.c.value).where(settings.c.key == 'plugin.core_test.message')).scalar_one() == '"retained"'
        change_selection(app, 1, 'core_test', 'enable')
        change_selection(app, 1, 'management_test', 'enable')
        with second.test_request_context():
            g.current_user = {'id': 1}
            assert read_settings('core_test')['message'] == 'retained'
            assert len(list_files('management_test')) == 1
    finally:
        second.extensions['neofab2_db'].dispose()


def test_typed_values_namespace_and_no_admin_wildcard(app):
    altered = replace(core, settings=(Setting('count', 2), Setting('enabled', False)),
                      permissions=(Permission('core_test.settings', ('staff',)),))
    app.extensions['neofab2_plugins'] = Registry([altered, plugin], ['core_test', 'management_test'])
    with app.test_request_context():
        g.current_user = {'id': 1}
        assert read_settings('core_test') == {'count': 2, 'enabled': False}
        with pytest.raises(PermissionError):
            save_settings('core_test', {'count': 3, 'enabled': True})
        for key in ('other', 'core', 'management_test'):
            with pytest.raises(PermissionError):
                read_settings(key)
    altered = replace(altered, permissions=core.permissions)
    app.extensions['neofab2_plugins'] = Registry([altered, plugin], ['core_test', 'management_test'])
    with app.test_request_context():
        g.current_user = {'id': 1}
        save_settings('core_test', {'count': 3, 'enabled': True})
        assert read_settings('core_test') == {'count': 3, 'enabled': True}
        with pytest.raises(ValueError):
            save_settings('core_test', {'count': True, 'enabled': 1})
        with app.extensions['neofab2_db'].begin() as conn:
            conn.execute(update(settings).where(settings.c.key == 'plugin.core_test.count').values(value='"invalid"'))
        with pytest.raises(ValueError, match='stored'):
            read_settings('core_test')


def test_successful_shared_commit_and_core_file_namespace(app):
    with app.test_request_context():
        g.current_user = {'id': 1}
        with write_transaction(app) as conn:
            save_settings('core_test', {'message': 'committed'}, connection=conn)
            key = store_file('management_test', FileStorage(stream=BytesIO(b'ok'), filename='ok.txt'), connection=conn)
        assert read_settings('core_test')['message'] == 'committed'
        assert list_files('management_test')[0]['id'] == key
        with pytest.raises(NotFound):
            list_files('core')
        with app.extensions['neofab2_db'].connect() as conn:
            with pytest.raises(ValueError):
                read_settings('core_test', connection=conn)


def test_settings_backup_restore_and_namespace_isolation(app, tmp_path):
    import sqlite3
    other = replace(plugin, settings=(Setting('message', 'other default'),),
                    settings_permission='management_test.check')
    app.extensions['neofab2_plugins'] = Registry([core, other], ['core_test', 'management_test'])
    with app.test_request_context():
        g.current_user = {'id': 1}
        save_settings('core_test', {'message': 'first'})
        save_settings('management_test', {'message': 'second'})
        assert read_settings('core_test')['message'] == 'first'
        assert read_settings('management_test')['message'] == 'second'
    restored_dir = tmp_path / 'restored'
    restored_dir.mkdir()
    with sqlite3.connect(tmp_path / 'neofab2.sqlite3') as source, sqlite3.connect(restored_dir / 'neofab2.sqlite3') as dest:
        source.backup(dest)
    restored = create_app({**app.config, 'DATA_DIR': str(restored_dir)})
    try:
        with restored.test_request_context():
            g.current_user = {'id': 1}
            assert read_settings('core_test')['message'] == 'first'
    finally:
        restored.extensions['neofab2_db'].dispose()


def test_engine_begin_rollback_does_not_commit_savepoint(app):
    with app.test_request_context():
        g.current_user = {'id': 1}
        with pytest.raises(RuntimeError):
            with app.extensions['neofab2_db'].begin() as conn:
                save_settings('core_test', {'message': 'never committed'}, connection=conn)
                raise RuntimeError('synthetic caller rollback')
        assert read_settings('core_test')['message'] == 'Synthetic test'
        with app.extensions['neofab2_db'].connect() as conn:
            assert conn.execute(select(events.c.id).where(events.c.module_id == 'core_test')).first() is None
