"""U09/N04: synthetic accounts only, including a read-only legacy snapshot."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from alembic import command
from click.testing import CliRunner
import pytest
from sqlalchemy import select, update, delete
from werkzeug.security import generate_password_hash, check_password_hash

from neofab2 import create_app
from neofab2.cli import main
from neofab2.database import upgrade_database, database_ready, migration_config
from neofab2.core.users import users, sessions, DETAIL_FIELDS, create_user
from neofab2.core.user_import import parse_export, preview, apply_import, links, compatible_hash, ImportFailure, MAX_BYTES
from neofab2.core.user_options import save_option
from neofab2.services.audit import events
from neofab2.services.legacy_users import export_snapshot
from neofab2.services.mail import outbox

PASSWORD = 'Synthetic123!'
HASH = generate_password_hash(PASSWORD, method='scrypt')


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.delenv('NEOFAB2_CONFIG', raising=False)
    app = create_app({'TESTING': True, 'SECRET_KEY': 's' * 64, 'DATA_DIR': str(tmp_path / 'data'),
                      'SESSION_COOKIE_SECURE': False})
    upgrade_database(app)
    create_user(app, 'admin@example.org', 'Local admin', PASSWORD, 'admin', bootstrap=True)
    create_user(app, 'user@example.org', 'Local user', PASSWORD, actor_id=1)
    create_user(app, 'staff@example.org', 'Local staff', PASSWORD, 'staff', actor_id=1)
    yield app
    app.extensions['neofab2_db'].dispose()


def source(**patch):
    row = dict(id=40, email='import@example.org', display_name='Synthetic import', role='worker',
               active=True, deleted=False, password_hash=HASH, locale='de', theme='dark', created_at=1700000000,
               details={name: '' for name in DETAIL_FIELDS})
    row.update(patch)
    return row


def raw(*rows, source_id='legacy-test'):
    return json.dumps({'format': 1, 'source': source_id, 'users': list(rows or [source()])}).encode()


def apply(app, data):
    report = preview(app, data, actor_id=1)
    return apply_import(app, data, report['plan'], actor_id=1)


def rows(app, table=users):
    with app.extensions['neofab2_db'].connect() as conn:
        return [dict(r) for r in conn.execute(select(table)).mappings()]


def csrf(client, path='/login'):
    return re.search(r'name="csrf_token" value="([^"]+)"', client.get(path).text).group(1)


def login(app, email='admin@example.org'):
    client = app.test_client()
    assert client.post('/login', data={'csrf_token': csrf(client), 'email': email, 'password': PASSWORD}).status_code == 302
    return client


def test_preview_is_readonly_and_report_has_no_credentials(app):
    before = rows(app), rows(app, links), rows(app, events), rows(app, outbox)
    report = preview(app, raw(), actor_id=1)
    assert report['counts']['create'] == 1
    assert not report['applied'] and report['rows'][0]['role'] == 'staff'
    assert HASH not in json.dumps(report) and 'password_hash' not in json.dumps(report)
    assert before == (rows(app), rows(app, links), rows(app, events), rows(app, outbox))


def test_import_repeat_restart_login_and_profile(app):
    record = source(details={**source()['details'], 'first_name': 'Synthetic', 'note': 'Private synthetic note'})
    report = apply(app, raw(record))
    uid = report['rows'][0]['user_id']
    assert report['applied']
    account = next(r for r in rows(app) if r['id'] == uid)
    assert account['role'] == 'staff' and account['active'] and not account['activation_pending']
    assert account['first_name'] == 'Synthetic' and account['locale'] == 'de' and account['theme'] == 'dark'
    assert account['created_at'] == 1700000000 and account['password_hash'] == HASH
    assert check_password_hash(account['password_hash'], PASSWORD)
    repeated = apply(app, raw(record))
    assert repeated['counts']['unchanged'] == 1 and len(rows(app)) == 4 and len(rows(app, links)) == 1
    assert len([r for r in rows(app, events) if r['event'] == 'user.imported']) == 1
    assert rows(app, outbox) == []
    restarted = create_app(dict(app.config))
    try:
        assert preview(restarted, raw(record), actor_id=1)['counts']['unchanged'] == 1
        assert login(restarted, 'import@example.org').get('/profile').status_code == 200
    finally:
        restarted.extensions['neofab2_db'].dispose()


@pytest.mark.parametrize('role,target', [('user','user'), ('worker','staff'), ('admin','admin')])
def test_roles(app, role, target):
    apply(app, raw(source(role=role)))
    assert rows(app)[-1]['role'] == target


@pytest.mark.parametrize('value', ['employee','staff','owner', '', [], 5])
def test_unknown_role_blocks_everything(app, value):
    data = raw(source(id=41, email='other@example.org'), source(role=value))
    report = preview(app, data, actor_id=1)
    assert report['counts']['conflict'] == 1
    with pytest.raises(ImportFailure, match='conflicts'):
        apply_import(app, data, report['plan'], actor_id=1)
    assert len(rows(app)) == 3 and not rows(app, links)


def test_inactive_deleted_and_invalid_hash(app):
    apply(app, raw(source(active=False), source(id=41, email='deleted@example.org', deleted=True),
                   source(id=42, email='reset@example.org', password_hash='invalid-secret')))
    accounts = rows(app)
    assert len(accounts) == 5
    inactive, reset = accounts[-2:]
    assert not inactive['active'] and not reset['active'] and reset['activation_pending']
    assert reset['password_hash'] != 'invalid-secret' and check_password_hash(reset['password_hash'], PASSWORD) is False
    for email in ('import@example.org', 'reset@example.org'):
        client = app.test_client()
        assert client.post('/login', data={'csrf_token': csrf(client), 'email': email, 'password': PASSWORD}).status_code == 401
    deleted_report = preview(app, raw(source(deleted=True)), actor_id=1)
    assert deleted_report['counts']['conflict'] == 1


@pytest.mark.parametrize('method', ['scrypt', 'pbkdf2:sha256:260000', 'pbkdf2:sha256:1000000'])
def test_compatible_hashes_login(app, method):
    hashed = generate_password_hash(PASSWORD, method=method)
    assert compatible_hash(hashed)
    apply(app, raw(source(password_hash=hashed)))
    assert login(app, 'import@example.org').get('/profile').status_code == 200


@pytest.mark.parametrize('hashed', ['md5$salt$ab', 'scrypt:1073741824:8:1$salt$'+'a'*128,
                                    'pbkdf2:sha256:999999999$salt$'+'a'*64, None, 'x'*513])
def test_hash_resource_limits(hashed):
    assert not compatible_hash(hashed)


@pytest.mark.parametrize('records,reason', [
    ([source(email='ADMIN@example.org')], 'email_collision'),
    ([source(),source(id=41,email='IMPORT@example.org')], 'duplicate_email'),
    ([source(details={**source()['details'], 'position': 'missing'})], 'unknown_option'),
])
def test_collisions_and_unknown_choices(app, records, reason):
    report = preview(app, raw(*records), actor_id=1)
    assert reason in [r['reason'] for r in report['rows']]
    with pytest.raises(ImportFailure):
        apply_import(app, raw(*records), report['plan'], actor_id=1)
    assert len(rows(app)) == 3


def test_known_profile_choices(app):
    save_option(app, 1, 'position', 'Synthetic position', True)
    apply(app, raw(source(details={**source()['details'], 'position':'Synthetic position'})))
    assert rows(app)[-1]['position'] == 'Synthetic position'


def test_changed_source_updates_and_revokes_sessions(app):
    apply(app, raw())
    client = login(app, 'import@example.org')
    data = raw(source(display_name='Changed', active=False))
    assert apply(app, data)['counts']['update'] == 1
    assert rows(app)[-1]['display_name'] == 'Changed' and not rows(app)[-1]['active']
    assert client.get('/profile').status_code == 302
    assert rows(app, sessions) == []


def test_local_changes_retained_and_conflict(app):
    apply(app, raw())
    uid = rows(app)[-1]['id']
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id == uid).values(active=False))
    assert apply(app, raw())['counts']['unchanged'] == 1
    assert not rows(app)[-1]['active']
    report = preview(app, raw(source(display_name='Changed source')), actor_id=1)
    assert report['rows'][0]['reason'] == 'local_changes'


@pytest.mark.parametrize('change', ['source','target','options','apply_twice'])
def test_stale_preview(app, change):
    data = raw()
    plan = preview(app, data, actor_id=1)['plan']
    if change == 'source':
        data = raw(source(display_name='Changed'))
    elif change == 'target':
        with app.extensions['neofab2_db'].begin() as conn:
            conn.execute(update(users).where(users.c.id == 2).values(display_name='Changed'))
    elif change == 'options':
        save_option(app, 1, 'position', 'New', True)
    else:
        apply_import(app, data, plan, actor_id=1)
    with pytest.raises(ImportFailure, match='stale'):
        apply_import(app, data, plan, actor_id=1)


def test_concurrent_apply_has_one_winner(app):
    plan = preview(app, raw(), actor_id=1)['plan']
    def run():
        try:
            return apply_import(app, raw(), plan, actor_id=1)['applied']
        except ImportFailure:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: run(), range(2))) == [False, True]
    assert len(rows(app, links)) == 1


def test_audit_failure_rolls_back_all(app, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('synthetic failure')
    monkeypatch.setattr('neofab2.core.user_import.record', fail)
    with pytest.raises(RuntimeError):
        apply(app, raw())
    assert len(rows(app)) == 3 and not rows(app, links)


@pytest.mark.parametrize('data', [b'{', b'\xff', b'{"format":1,"format":1}', b'[]',
                                   b'{"version":"0.9.62","users":[]}', b'x'*(MAX_BYTES+1)])
def test_invalid_format(data):
    with pytest.raises(ImportFailure):
        parse_export(data)


def test_duplicate_ids_extra_fields_and_tokens_rejected():
    with pytest.raises(ImportFailure):
        parse_export(raw(source(), source()))
    with pytest.raises(ImportFailure):
        parse_export(raw(source(token='never-import')))


@pytest.mark.parametrize('actor', [2,3,999])
def test_admin_permission(app, actor):
    with pytest.raises(PermissionError):
        preview(app, raw(), actor_id=actor)
    with pytest.raises(PermissionError):
        apply_import(app, raw(), 'invalid', actor_id=actor)


def test_revoked_admin(app):
    plan = preview(app, raw(), actor_id=1)['plan']
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id == 1).values(active=False))
    with pytest.raises(PermissionError):
        apply_import(app, raw(), plan, actor_id=1)


def test_last_admin_guard(app):
    apply(app, raw(source(role='admin')))
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id == 1).values(active=False))
    report = preview(app, raw(source(role='user')), operator=True)
    assert report['counts']['conflict'] == 1
    assert report['rows'][-1]['reason'] == 'last_admin'


def legacy_db(path, records=None):
    records = records or [source()]
    names = ['id','email','password_hash','role','language','theme_mode','is_active','deleted_at','created_at', *DETAIL_FIELDS]
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE user (' + ','.join(f'"{n}" {"INTEGER" if n in ("id","is_active") else "TEXT"}' for n in names) + ')')
        conn.execute('CREATE TABLE user_activation_tokens (token_hash TEXT)')
        conn.execute("INSERT INTO user_activation_tokens VALUES ('never-import-token')")
        for row in records:
            data = [row['id'],row['email'],row['password_hash'],row['role'],row['locale'],row['theme'],int(row['active']),
                    '2020-01-01' if row['deleted'] else None,'2023-11-14T22:13:20',*row['details'].values()]
            conn.execute('INSERT INTO user VALUES ('+','.join('?' for _ in data)+')', data)
    return path


def test_legacy_snapshot_readonly_and_deleted_privacy(tmp_path):
    path = legacy_db(tmp_path/'snapshot.sqlite3', [source(),source(id=41,deleted=True,email='deleted-secret@example.org')])
    before = path.read_bytes()
    exported = export_snapshot(path, 'legacy-test')
    assert path.read_bytes() == before
    assert b'never-import-token' not in exported and b'deleted-secret' not in exported
    data = parse_export(exported)
    assert data['users'][0]['theme'] == 'dark' and data['users'][0]['created_at'] == 1700000000
    assert data['users'][0]['id'] == 40 and data['users'][1]['deleted']


def test_missing_source_never_created(tmp_path):
    path = tmp_path/'missing.sqlite3'
    with pytest.raises(ImportFailure):
        export_snapshot(path,'legacy-test')
    assert not path.exists()


def test_migration_from_017_and_restore(tmp_path, monkeypatch):
    monkeypatch.delenv('NEOFAB2_CONFIG', raising=False)
    app = create_app({'TESTING': True,'SECRET_KEY':'s'*64,'DATA_DIR':str(tmp_path/'db')})
    (tmp_path/'db').mkdir()
    try:
        config = migration_config()
        with app.extensions['neofab2_db'].begin() as conn:
            config.attributes['connection'] = conn
            command.upgrade(config, '0011_audit_status')
        create_user(app,'admin@example.org','Admin',PASSWORD,'admin',bootstrap=True)
        before = rows(app)
        assert not database_ready(app)
        upgrade_database(app)
        upgrade_database(app)
        assert database_ready(app) and rows(app) == before and rows(app, links) == []
        apply(app,raw())
        restored_dir = tmp_path/'restore'
        restored_dir.mkdir()
        with sqlite3.connect(tmp_path/'db'/'neofab2.sqlite3') as src, sqlite3.connect(restored_dir/'neofab2.sqlite3') as dst:
            src.backup(dst)
        restored = create_app({**app.config,'DATA_DIR':str(restored_dir)})
        try:
            assert preview(restored,raw(),actor_id=1)['counts']['unchanged'] == 1
        finally:
            restored.extensions['neofab2_db'].dispose()
        with app.extensions['neofab2_db'].begin() as conn:
            conn.exec_driver_sql('DROP TABLE core_user_imports')
        assert not database_ready(app)
    finally:
        app.extensions['neofab2_db'].dispose()


def post_import(client, data, action='preview', **extra):
    from io import BytesIO
    return client.post('/admin/users/import', data={'csrf_token':csrf(client,'/admin/users/import'),
        'action':action, 'file':(BytesIO(data),'users.json'), **extra})


def test_web_preview_apply_report_permissions_and_csrf(app):
    from io import BytesIO
    assert app.test_client().get('/admin/users/import').status_code == 302
    for email in ('user@example.org','staff@example.org'):
        client = login(app,email)
        assert client.get('/admin/users/import').status_code == 403
        assert client.post('/admin/users/import', data={'csrf_token':csrf(client,'/profile'),
            'action':'apply','file':(BytesIO(raw()),'users.json')}).status_code == 403
    admin = login(app)
    assert admin.post('/admin/users/import', data={'file':(BytesIO(raw()),'users.json')}).status_code == 400
    page = post_import(admin, raw())
    assert page.status_code == 200 and 'Import preview' in page.text
    assert HASH not in page.text and 'password_hash' not in page.text
    assert len(rows(app)) == 3
    plan = re.search(r'name="plan" value="([^"]+)"',page.text).group(1)
    assert post_import(admin, raw(), action='apply', plan=plan).status_code == 400
    result = post_import(admin, raw(), action='apply', plan=plan,confirm='yes')
    assert result.status_code == 200 and 'Import result' in result.text
    assert HASH not in result.text and len(rows(app)) == 4
    assert post_import(admin, raw(), action='apply', plan=plan,confirm='yes').status_code == 400
    with admin.session_transaction() as session:
        assert HASH not in str(dict(session))


def test_web_errors_and_translation_do_not_reflect_secrets(app):
    from io import BytesIO
    admin = login(app)
    data = raw(source(role='<script>secret-role</script>', password_hash='secret-hash'))
    result = post_import(admin, data)
    assert result.status_code == 200 and 'Invalid account fields' in result.text
    assert 'secret-role' not in result.text and 'secret-hash' not in result.text
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id == 1).values(locale='de'))
    assert 'Benutzerimport' in admin.get('/admin/users/import').text
    assert post_import(admin, b'{').status_code == 400
    assert admin.post('/admin/users/import',data={'csrf_token':csrf(admin,'/admin/users/import'),'action':'preview'}).status_code == 400
    assert post_import(admin,b'x'*1048577).status_code == 413


def configure_cli(app,tmp_path,monkeypatch):
    config = tmp_path/'import-config.toml'
    config.write_text('SECRET_KEY = '+json.dumps(app.config['SECRET_KEY'])+'\nDATA_DIR = '+json.dumps(app.config['DATA_DIR'])+'\n')
    monkeypatch.setenv('NEOFAB2_CONFIG',str(config))


def test_cli_export_preview_confirmation_report_and_permissions(app,tmp_path,monkeypatch):
    configure_cli(app,tmp_path,monkeypatch)
    runner = CliRunner()
    snapshot = legacy_db(tmp_path/'old.sqlite3')
    exported = tmp_path/'users.json'
    command = ['prepare-user-import','--database',str(snapshot),'--source-id','legacy-test','--output',str(exported)]
    result = runner.invoke(main,command)
    assert result.exit_code == 0, result.output
    assert exported.stat().st_mode & 0o777 == 0o600
    before = exported.read_bytes()
    assert runner.invoke(main,command).exit_code == 1 and exported.read_bytes() == before
    result = runner.invoke(main,['users-import',str(exported)])
    assert result.exit_code == 0 and HASH not in result.output and 'password_hash' not in result.output
    report = json.loads(result.output)
    assert len(rows(app)) == 3
    args = ['users-import',str(exported),'--apply','--expected-plan',report['plan']]
    assert runner.invoke(main,args,input='n\n').exit_code == 1 and len(rows(app)) == 3
    result = runner.invoke(main,args,input='y\n')
    assert result.exit_code == 0, result.output
    assert HASH not in result.output and len(rows(app)) == 4
    assert runner.invoke(main,args,input='y\n').exit_code == 1
    repeat = runner.invoke(main,['users-import',str(exported)])
    assert json.loads(repeat.output)['counts']['unchanged'] == 1


def test_cli_rejects_conflicts_and_no_confirmation_plan(app,tmp_path,monkeypatch):
    configure_cli(app,tmp_path,monkeypatch)
    path = tmp_path/'synthetic.json'
    path.write_bytes(raw())
    runner = CliRunner()
    result = runner.invoke(main,['users-import',str(path),'--apply'],input='y\n')
    assert result.exit_code == 1 and len(rows(app)) == 3
    path.write_bytes(raw(source(email='admin@example.org')))
    assert runner.invoke(main,['users-import',str(path)]).exit_code == 1


def test_database_error_does_not_leak_hash_in_web_or_cli(app,tmp_path,monkeypatch,caplog):
    from sqlalchemy.exc import IntegrityError
    def fail(*args,**kwargs):
        raise IntegrityError('synthetic SQL', {'password_hash':HASH}, Exception('synthetic'))
    monkeypatch.setattr('neofab2.core.user_import.record',fail)
    admin=login(app)
    plan = preview(app,raw(),actor_id=1)['plan']
    result=post_import(admin,raw(),action='apply',plan=plan,confirm='yes')
    assert result.status_code == 400 and HASH not in result.text and HASH not in caplog.text
    assert len(rows(app)) == 3 and not rows(app,links)
    configure_cli(app,tmp_path,monkeypatch)
    path=tmp_path/'synthetic.json'
    path.write_bytes(raw())
    result=CliRunner().invoke(main,['users-import',str(path),'--apply','--expected-plan',plan],input='y\n')
    assert result.exit_code == 1 and HASH not in result.output and len(rows(app)) == 3


def test_update_invalidates_account_tokens(app):
    from neofab2.core.account_flows import tokens
    apply(app,raw())
    uid=rows(app)[-1]['id']
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(tokens.insert().values(id='c'*32,user_id=uid,purpose='reset',token_hash='a'*64,
            fingerprint='b'*64,created_at=1,expires_at=9999999999))
    apply(app,raw(source(display_name='Changed')))
    with app.extensions['neofab2_db'].connect() as conn:
        assert conn.execute(select(tokens.c.used_at).where(tokens.c.user_id==uid)).scalar_one() is not None


def test_source_id_namespace_and_missing_rows_never_delete(app):
    apply(app,raw())
    report=preview(app,raw(source(),source_id='another-installation'),actor_id=1)
    assert report['counts']['conflict']==1
    empty=json.dumps({'format':1,'source':'legacy-test','users':[]}).encode()
    assert apply(app,empty)['applied'] and len(rows(app))==4


def test_snapshot_rejects_views_wal_and_wrong_schema(tmp_path):
    view=tmp_path/'view.sqlite3'
    with sqlite3.connect(view) as conn:
        conn.execute('CREATE VIEW user AS SELECT 1 AS id')
    with pytest.raises(ImportFailure):
        export_snapshot(view,'legacy-test')
    snapshot=legacy_db(tmp_path/'wal.sqlite3')
    Path(str(snapshot)+'-wal').write_bytes(b'synthetic')
    with pytest.raises(ImportFailure):
        export_snapshot(snapshot,'legacy-test')


@pytest.mark.parametrize('plan', ['é', '', 'x' * 64, None])
def test_invalid_plan_rejected_without_writes(app, plan):
    with pytest.raises(ImportFailure, match='stale'):
        apply_import(app, raw(), plan, actor_id=1)
    assert len(rows(app)) == 3
