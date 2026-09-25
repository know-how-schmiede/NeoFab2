"""Confirmed deletion of inactive accounts; unknown ownership fails closed."""
import hashlib
import json

from itsdangerous import URLSafeTimedSerializer, BadData
from sqlalchemy import select, delete, update, inspect, or_, func
from werkzeug.exceptions import NotFound

from .users import users, sessions, attempts, require_actor, write_transaction, reserve_user_id
from .account_flows import tokens, limits
from .user_import import links
from neofab2.services.files import files
from neofab2.services.mail import outbox, mailbox
from neofab2.services.audit import record

KNOWN_TABLES = {'alembic_version', 'core_settings', 'core_users', 'core_sessions',
    'core_login_attempts', 'core_user_options', 'core_files', 'core_mail_outbox',
    'core_account_tokens', 'core_account_limits', 'core_audit_events', 'core_worker_status', 'core_user_imports'}
KNOWN_PLUGINS = {'core_test', 'management_test', 'checkdesign'}


def signer(app):
    return URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='user-delete-v1')


def _preview(app, conn, actor_id, user_id):
    require_actor(conn, actor_id)
    account = conn.execute(select(users).where(users.c.id == user_id)).mappings().first()
    if account is None:
        raise NotFound()
    if user_id == actor_id or account['active']:
        raise ValueError('Only a disabled account other than your own can be deleted.')
    owned_files = conn.execute(select(files.c.id).where(files.c.owner_id == user_id).order_by(files.c.id)).scalars().all()
    linked = [dict(r) for r in conn.execute(select(links).where(links.c.user_id == user_id).order_by(links.c.source, links.c.source_id)).mappings()]
    recipients = {account['email']}
    try:
        recipients.add(mailbox(account['email']))
    except ValueError:
        pass
    mails = [dict(r) for r in conn.execute(select(outbox).where(or_(
        outbox.c.account_user_id == user_id, func.lower(outbox.c.recipient).in_({address.lower() for address in recipients}))).order_by(outbox.c.id)).mappings()]
    session_rows = [dict(r) for r in conn.execute(select(sessions).where(sessions.c.user_id == user_id).order_by(sessions.c.token_hash)).mappings()]
    token_rows = [dict(r) for r in conn.execute(select(tokens).where(tokens.c.user_id == user_id).order_by(tokens.c.id)).mappings()]
    unknown = bool(set(inspect(conn).get_table_names()) - KNOWN_TABLES or
                   set(app.extensions['neofab2_plugins'].available) - KNOWN_PLUGINS)
    blockers = []
    if owned_files:
        blockers.append('This account owns files. Deletion is blocked to preserve their ownership.')
    if unknown:
        blockers.append('Unreviewed plugin or database references prevent account deletion.')
    if any(m['account_user_id'] != user_id or m['module_id'] != 'core' for m in mails):
        blockers.append('Other mail records refer to this account. Deletion is blocked.')
    if any(m['status'] in ('sending', 'uncertain') for m in mails):
        blockers.append('Mail delivery is in progress or uncertain. Resolve it before deleting this account.')
    state = hashlib.sha256(json.dumps([dict(account), linked, mails, session_rows, token_rows, owned_files, unknown],
                                      sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'entry': {key: account[key] for key in ('id', 'email', 'display_name')}, 'blockers': blockers,
            'counts': {'sessions': len(session_rows), 'tokens': len(token_rows), 'mail': len(mails), 'imports': len(linked)},
            'state': state}


def deletion_preview(app, actor_id, user_id):
    with app.extensions['neofab2_db'].connect() as conn:
        conn.exec_driver_sql('BEGIN')
        preview = _preview(app, conn, actor_id, user_id)
    preview['confirmation'] = signer(app).dumps([actor_id, user_id, preview.pop('state')])
    return preview


def delete_disabled_user(app, actor_id, user_id, confirmation):
    try:
        signed = signer(app).loads(confirmation or '', max_age=600)
    except (BadData, TypeError):
        raise ValueError('The deletion confirmation has expired or is invalid. Review the account again.') from None
    with write_transaction(app) as conn:
        preview = _preview(app, conn, actor_id, user_id)
        if signed != [actor_id, user_id, preview['state']]:
            raise ValueError('The account or its references changed. Review the deletion again.')
        if preview['blockers']:
            raise ValueError(preview['blockers'][0])
        # Reserve beyond the current maximum before deleting, even for older databases.
        reserve_user_id(conn)
        conn.execute(delete(outbox).where(outbox.c.account_user_id == user_id))
        conn.execute(delete(tokens).where(tokens.c.user_id == user_id))
        conn.execute(delete(sessions).where(sessions.c.user_id == user_id))
        conn.execute(update(links).where(links.c.user_id == user_id).values(user_id=None))
        from .auth import attempt_key
        conn.execute(delete(attempts).where(attempts.c.key == attempt_key(app, 'account', preview['entry']['email'])))
        conn.execute(delete(limits).where(limits.c.key == attempt_key(app, 'selfservice:email', preview['entry']['email'])))
        conn.execute(delete(users).where(users.c.id == user_id))
        record(conn, 'user.deleted', actor_id=actor_id, target_id=user_id)
