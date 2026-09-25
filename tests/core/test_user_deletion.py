"""S01/U05: toolbar and explicit, state-bound inactive account deletion."""
from dataclasses import replace
import re
import sqlite3

from alembic import command
import pytest
from sqlalchemy import select, update
from werkzeug.exceptions import NotFound

from neofab2 import create_app
from neofab2.core.users import users, sessions, create_user
from neofab2.core.account_flows import tokens
from neofab2.core.user_deletion import deletion_preview, delete_disabled_user
from neofab2.core.user_import import links, preview, apply_import
from neofab2.core.settings import settings
from neofab2.services.files import files
from neofab2.services.mail import outbox, enqueue
from neofab2.services.audit import events
from neofab2.database import upgrade_database, migration_config, database_ready
from test_user_import import app, login, csrf, rows, raw, source, PASSWORD, apply


def disable(app, user_id=2):
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id==user_id).values(active=False))


def confirmation(client, uid=2):
    response=client.get(f'/admin/users/{uid}/delete')
    assert response.status_code==200
    return re.search(r'name="confirmation" value="([^"]+)"',response.text).group(1)


def perform(app, uid=2):
    planned=deletion_preview(app,1,uid)
    delete_disabled_user(app,1,uid,planned['confirmation'])


def test_toolbar_and_edit_visibility(app):
    admin=login(app)
    page=admin.get('/admin/users').text
    bar=page.split('class="button-bar"',1)[1].split('</div>',1)[0]
    assert bar.index('Create user')<bar.index('Export users')<bar.index('Import users')
    assert bar.count('class="button"')==2 and '<button type="submit"' in bar
    assert 'class="card-form"' not in page
    assert '/admin/users/2/delete' not in admin.get('/admin/users/2/edit').text
    disable(app)
    assert '/admin/users/2/delete' in admin.get('/admin/users/2/edit').text
    assert '/delete' not in admin.get('/admin/users/new').text


def test_preview_cancel_and_confirmed_http_deletion(app):
    disable(app)
    admin=login(app)
    before=rows(app)
    plan=confirmation(admin)
    assert rows(app)==before
    assert admin.get('/admin/users/2/edit').status_code==200 # Cancel target is read-only.
    data={'csrf_token':csrf(admin,'/admin/users/2/edit'),'confirmation':plan}
    assert admin.post('/admin/users/2/delete',data=data).status_code==400
    assert rows(app)==before
    response=admin.post('/admin/users/2/delete',data={**data,'confirm':'yes'})
    assert response.status_code==302 and response.location=='/admin/users'
    assert len(rows(app))==2
    assert admin.get('/admin/users/2/edit').status_code==404
    assert admin.post('/admin/users/2/delete',data={**data,'confirm':'yes'}).status_code==404
    audit=[r for r in rows(app,events) if r['event']=='user.deleted']
    assert len(audit)==1 and audit[0]['target_id']==2 and audit[0]['actor_id']==1
    assert 'user@example.org' not in str(audit)


def test_delete_owned_security_records_atomically(app):
    disable(app)
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(sessions.insert().values(token_hash='a'*64,user_id=2,created_at=1,last_seen=1))
        conn.execute(tokens.insert().values(id='b'*32,user_id=2,purpose='reset',token_hash='c'*64,
            fingerprint='d'*64,created_at=1,expires_at=9999999999))
        job=enqueue(conn,'core','synthetic-delete','user@example.org','Synthetic','Synthetic')
        conn.execute(update(outbox).where(outbox.c.id==job).values(account_user_id=2))
    plan=deletion_preview(app,1,2)
    assert plan['counts']=={'sessions':1,'tokens':1,'mail':1,'imports':0}
    delete_disabled_user(app,1,2,plan['confirmation'])
    assert rows(app,sessions)==[] and rows(app,tokens)==[] and rows(app,outbox)==[]


@pytest.mark.parametrize('uid',[1,2,3])
def test_active_or_self_never_deletable(app,uid):
    with pytest.raises(ValueError):
        deletion_preview(app,1,uid)
    with pytest.raises(ValueError):
        delete_disabled_user(app,1,uid,'fake')
    assert len(rows(app))==3


@pytest.mark.parametrize('actor',[2,3,999])
def test_admin_and_direct_http_rights(app,actor):
    disable(app,3)
    with pytest.raises(PermissionError):
        deletion_preview(app,actor,3)
    user=login(app,'user@example.org')
    assert user.get('/admin/users/3/delete').status_code==403
    assert user.post('/admin/users/3/delete',data={'csrf_token':csrf(user,'/profile'),'confirm':'yes'}).status_code==403


def test_csrf_and_forged_confirmation(app):
    disable(app)
    admin=login(app)
    plan=confirmation(admin)
    assert admin.post('/admin/users/2/delete',data={'confirmation':plan,'confirm':'yes'}).status_code==400
    assert admin.post('/admin/users/2/delete',data={'csrf_token':csrf(admin,'/admin/users'),'confirmation':'fake','confirm':'yes'}).status_code==400
    assert len(rows(app))==3


@pytest.mark.parametrize('change',['profile','active','new_mail','actor','other_account'])
def test_stale_or_wrong_confirmation(app,change):
    disable(app)
    plan=deletion_preview(app,1,2)['confirmation']
    with app.extensions['neofab2_db'].begin() as conn:
        if change=='profile':
            conn.execute(update(users).where(users.c.id==2).values(display_name='Changed'))
        elif change=='active':
            conn.execute(update(users).where(users.c.id==2).values(active=True))
        elif change=='new_mail':
            enqueue(conn,'core','new-synthetic','user@example.org','Synthetic','Synthetic')
        elif change=='actor':
            conn.execute(update(users).where(users.c.id==1).values(active=False))
        else:
            conn.execute(update(users).where(users.c.id==3).values(active=False))
    with pytest.raises(PermissionError if change=='actor' else ValueError):
        delete_disabled_user(app,1,3 if change=='other_account' else 2,plan)
    assert len(rows(app))==3


def test_expired_confirmation(app,monkeypatch):
    disable(app)
    import time
    now=time.time()
    monkeypatch.setattr('itsdangerous.timed.time.time',lambda:now-601)
    plan=deletion_preview(app,1,2)['confirmation']
    monkeypatch.setattr('itsdangerous.timed.time.time',lambda:now)
    with pytest.raises(ValueError,match='expired'):
        delete_disabled_user(app,1,2,plan)


@pytest.mark.parametrize('reference',['file','unknown_table','unknown_plugin','sending','uncertain','generic_mail'])
def test_references_block_without_deleting(app,reference):
    disable(app)
    with app.extensions['neofab2_db'].begin() as conn:
        if reference=='file':
            conn.execute(files.insert().values(id='f'*32,plugin_id='management_test',owner_id=2,
                filename='synthetic.txt',size=1,created_at=1,content=b'x'))
        elif reference=='unknown_table':
            conn.exec_driver_sql('CREATE TABLE plugin_synthetic (user_id INTEGER)')
        elif reference=='unknown_plugin':
            from neofab2.plugin_api.registry import Registry
            from neofab2.plugins.management_test import plugin
            unknown=replace(plugin,plugin_id='synthetic',permission='synthetic.access',permissions=(),files=None,dependencies=())
            app.extensions['neofab2_plugins']=Registry([unknown],[])
        else:
            job=enqueue(conn,'core','synthetic-ref','user@example.org','Synthetic','Synthetic')
            if reference!='generic_mail':
                conn.execute(update(outbox).where(outbox.c.id==job).values(account_user_id=2,status=reference))
    plan=deletion_preview(app,1,2)
    assert plan['blockers']
    with pytest.raises(ValueError):
        delete_disabled_user(app,1,2,plan['confirmation'])
    assert len(rows(app))==3


def test_import_marker_prevents_recreation_and_ids_not_reused(app):
    imported=apply(app,raw(source(active=False)))
    uid=imported['rows'][0]['user_id']
    perform(app,uid)
    assert rows(app,links)[0]['user_id'] is None
    for data in (raw(source(active=False)),raw(source(active=True))):
        report=preview(app,data,actor_id=1)
        assert report['rows'][0]['reason']=='target_deleted'
        with pytest.raises(ValueError):
            apply_import(app,data,report['plan'],actor_id=1)
    next_id=create_user(app,'new@example.org','New synthetic',PASSWORD,actor_id=1)
    assert next_id>uid


def test_audit_error_rolls_back_account_mail_and_counter(app,monkeypatch):
    disable(app)
    before=rows(app,settings)
    def fail(*args,**kwargs):
        raise RuntimeError('synthetic')
    monkeypatch.setattr('neofab2.core.user_deletion.record',fail)
    with pytest.raises(RuntimeError):
        perform(app)
    assert len(rows(app))==3 and rows(app,settings)==before


def test_unknown_id_404_and_confirmation_escapes_name(app):
    disable(app)
    with app.extensions['neofab2_db'].begin() as conn:
        conn.execute(update(users).where(users.c.id==2).values(display_name='<script>synthetic</script>'))
    admin=login(app)
    page=admin.get('/admin/users/2/delete')
    assert '&lt;script&gt;' in page.text and '<script>' not in page.text
    assert admin.get('/admin/users/999/delete').status_code==404


def test_upgrade_from_0012_and_restore_marker(tmp_path,monkeypatch):
    monkeypatch.delenv('NEOFAB2_CONFIG',raising=False)
    folder=tmp_path/'db'
    folder.mkdir()
    app=create_app({'TESTING':True,'SECRET_KEY':'s'*64,'DATA_DIR':str(folder)})
    try:
        config=migration_config()
        with app.extensions['neofab2_db'].begin() as conn:
            config.attributes['connection']=conn
            command.upgrade(config,'0012_user_import')
        create_user(app,'admin@example.org','Admin',PASSWORD,'admin',bootstrap=True)
        imported=apply(app,raw(source(active=False)))
        old=rows(app,links)
        assert not database_ready(app)
        upgrade_database(app)
        upgrade_database(app)
        assert database_ready(app) and rows(app,links)==old
        uid=imported['rows'][0]['user_id']
        perform(app,uid)
        restored_folder=tmp_path/'restore'
        restored_folder.mkdir()
        with sqlite3.connect(folder/'neofab2.sqlite3') as src,sqlite3.connect(restored_folder/'neofab2.sqlite3') as dst:
            src.backup(dst)
        restored=create_app({**app.config,'DATA_DIR':str(restored_folder)})
        try:
            assert preview(restored,raw(source(active=False)),actor_id=1)['counts']['conflict']==1
            assert create_user(restored,'other@example.org','Other',PASSWORD,actor_id=1)>uid
        finally:
            restored.extensions['neofab2_db'].dispose()
    finally:
        app.extensions['neofab2_db'].dispose()
