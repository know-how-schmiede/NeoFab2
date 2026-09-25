"""U09: protected, bounded NeoFab2 account export, without sessions or tokens."""
import json
import re
import secrets

from sqlalchemy import select

from .settings import settings
from .users import users, DETAIL_FIELDS, require_actor, write_transaction
from .user_import import MAX_BYTES, MAX_USERS, ImportFailure
from neofab2.services.audit import record

SOURCE_KEY = 'core.users.export_source'


def export_users(app, *, actor_id=None, operator=False):
    with write_transaction(app) as conn:
        if not operator:
            require_actor(conn, actor_id)
        source = conn.execute(select(settings.c.value).where(settings.c.key == SOURCE_KEY)).scalar_one_or_none()
        if source is None:
            source = 'neofab2-' + secrets.token_hex(16)
            conn.execute(settings.insert().values(key=SOURCE_KEY, value=source))
        if not re.fullmatch(r'neofab2-[0-9a-f]{32}', source):
            raise ImportFailure('Invalid saved export identity. Restore a valid backup.')
        accounts = conn.execute(select(users).order_by(users.c.id).limit(MAX_USERS + 1)).mappings().all()
        if len(accounts) > MAX_USERS:
            raise ImportFailure('Too many accounts for a user export.')
        entries = []
        for account in accounts:
            entry = {name: account[name] for name in (
                'id', 'email', 'display_name', 'role', 'active', 'activation_pending',
                'password_hash', 'locale', 'theme', 'created_at')}
            entry.update(deleted=False, details={name: account[name] for name in DETAIL_FIELDS})
            entries.append(entry)
        raw = json.dumps({'format': 2, 'source': source, 'users': entries}, ensure_ascii=True, indent=2).encode('utf-8')
        if len(raw) > MAX_BYTES:
            raise ImportFailure('User export exceeds the size limit.')
        record(conn, 'users.exported', actor_id=actor_id, count=len(entries))
        return raw
