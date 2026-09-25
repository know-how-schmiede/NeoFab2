"""U09: private native export and lossless account-state import, synthetic only."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy import select, update

from neofab2 import create_app
from neofab2.cli import main
from neofab2.database import upgrade_database
from neofab2.core.user_export import export_users, SOURCE_KEY
from neofab2.core.user_import import parse_export, preview, apply_import, ImportFailure
from neofab2.core.users import users
from neofab2.core.settings import settings
from neofab2.services.audit import events
from test_user_import import app, login, csrf, rows, configure_cli


def test_web_download_all_accounts_headers_and_audit(app):
    admin = login(app)
    page = admin.get('/admin/users')
    assert 'Export users' in page.text
    response = admin.post('/admin/users/export', data={'csrf_token':csrf(admin,'/admin/users')})
    assert response.status_code == 200 and response.mimetype == 'application/json'
    assert 'attachment;' in response.headers['Content-Disposition']
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    payload = parse_export(response.data)
    assert payload['format'] == 2 and len(payload['users']) == 3
    assert payload['users'][2]['role'] == 'staff'
    assert 'sessions' not in payload and 'tokens' not in payload
    with app.extensions['neofab2_db'].connect() as conn:
        event = conn.execute(select(events).where(events.c.event=='users.exported')).mappings().one()
        assert event['actor_id'] == 1 and event['count'] == 3
        assert payload['users'][0]['password_hash'] not in str(event)
    assert payload['users'][0]['password_hash'] not in page.text


def test_permissions_csrf_and_current_status(app):
    assert app.test_client().post('/admin/users/export').status_code in (302,400)
    for email in ('user@example.org','staff@example.org'):
        client=login(app,email)
        assert client.post('/admin/users/export',data={'csrf_token':csrf(client,'/profile')}).status_code==403
    admin=login(app)
    assert admin.get('/admin/users/export').status_code==405
    assert admin.post('/admin/users/export').status_code==400
    for actor in (2,3,999):
        with pytest.raises(PermissionError):
            export_users(app,actor_id=actor)
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id==1).values(activation_pending=True))
    with pytest.raises(PermissionError):
        export_users(app,actor_id=1)


def test_identity_stable_concurrent_and_restart(app):
    with ThreadPoolExecutor(max_workers=2) as pool:
        exports=list(pool.map(lambda _: export_users(app,actor_id=1),range(2)))
    assert exports[0]==exports[1]
    other=create_app(dict(app.config))
    try:
        assert export_users(other,actor_id=1)==exports[0]
    finally:
        other.extensions['neofab2_db'].dispose()


def test_roundtrip_preserves_password_profiles_and_pending(app,tmp_path):
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id==2).values(active=False,activation_pending=True,
            locale='fr',theme='light',first_name='Synthetic',note='Synthetic note'))
        conn.execute(update(users).where(users.c.id==3).values(active=False))
    before=rows(app)
    exported=export_users(app,actor_id=1)
    other=create_app({**app.config,'DATA_DIR':str(tmp_path/'destination')})
    try:
        upgrade_database(other)
        plan=preview(other,exported,operator=True)
        assert plan['counts']['create']==3 and not plan['counts']['conflict']
        apply_import(other,exported,plan['plan'],operator=True)
        assert rows(other)==before
        assert preview(other,exported,operator=True)['counts']['unchanged']==3
        assert preview(app,exported,actor_id=1)['counts']['conflict']==3
    finally:
        other.extensions['neofab2_db'].dispose()


@pytest.mark.parametrize('pending',[None,1,'false',[]])
def test_native_pending_is_strict_boolean(app,pending):
    payload=json.loads(export_users(app,actor_id=1))
    payload['users'][0]['activation_pending']=pending
    report=preview(app,json.dumps(payload).encode(),actor_id=1)
    assert report['rows'][0]['reason']=='invalid_fields'


def test_native_role_does_not_loosen_legacy_contract(app):
    payload=json.loads(export_users(app,actor_id=1))
    payload['users'][0]['role']='worker'
    assert preview(app,json.dumps(payload).encode(),actor_id=1)['rows'][0]['reason']=='invalid_fields'
    del payload['users'][0]['activation_pending']
    with pytest.raises(ImportFailure):
        parse_export(json.dumps(payload).encode())


@pytest.mark.parametrize('limit',[('MAX_USERS',2),('MAX_BYTES',10)])
def test_limits_abort_without_identity_or_audit(app,monkeypatch,limit):
    monkeypatch.setattr('neofab2.core.user_export.'+limit[0],limit[1])
    with pytest.raises(ImportFailure):
        export_users(app,actor_id=1)
    with app.extensions['neofab2_db'].connect() as conn:
        assert conn.execute(select(settings).where(settings.c.key==SOURCE_KEY)).first() is None
        assert conn.execute(select(events).where(events.c.event=='users.exported')).first() is None


def test_audit_failure_blocks_delivery_and_hides_hashes(app,monkeypatch,caplog):
    from sqlalchemy.exc import IntegrityError
    secret=rows(app)[0]['password_hash']
    def fail(*args,**kwargs):
        raise IntegrityError('synthetic',{'password_hash':secret},Exception('synthetic'))
    monkeypatch.setattr('neofab2.core.user_export.record',fail)
    client=login(app)
    result=client.post('/admin/users/export',data={'csrf_token':csrf(client,'/admin/users')})
    assert result.status_code==503 and secret not in result.text and secret not in caplog.text
    with app.extensions['neofab2_db'].connect() as conn:
        assert conn.execute(select(settings).where(settings.c.key==SOURCE_KEY)).first() is None


def test_cli_private_file_no_overwrite_or_hash_output(app,tmp_path,monkeypatch):
    configure_cli(app,tmp_path,monkeypatch)
    output=tmp_path/'native-users.json'
    runner=CliRunner()
    args=['users-export','--output',str(output)]
    result=runner.invoke(main,args)
    assert result.exit_code==0,result.output
    assert output.stat().st_mode & 0o777==0o600
    data=output.read_bytes()
    assert parse_export(data)['format']==2
    assert rows(app)[0]['password_hash'] not in result.output
    assert runner.invoke(main,args).exit_code==1 and output.read_bytes()==data


def test_invalid_saved_identity_not_silently_replaced(app):
    export_users(app,actor_id=1)
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(settings).where(settings.c.key==SOURCE_KEY).values(value='bad'))
    with pytest.raises(ImportFailure):
        export_users(app,actor_id=1)
