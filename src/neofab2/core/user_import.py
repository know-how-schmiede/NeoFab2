"""U09/N04: bounded, previewed, atomic account import. No source writes or mail."""
import hashlib
import hmac
import json
import re
import secrets

from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, select, delete, update

from .users import (users, sessions, DETAIL_FIELDS, normalize_email, validate_name,
                    validate_details, require_actor, write_transaction, hash_password)
from .user_options import options, validate_choices
from neofab2.services.audit import record

MAX_BYTES = 8 * 1024 * 1024
MAX_USERS = 5000
ROLE_MAP = {"user": "user", "worker": "staff", "admin": "admin"}
links = Table("core_user_imports", MetaData(),
    Column("source", String(64), primary_key=True), Column("source_id", BigInteger, primary_key=True),
    Column("user_id", Integer), Column("source_digest", String(64)), Column("target_digest", String(64)))
FIELDS = {"id", "email", "display_name", "role", "active", "deleted", "password_hash", "locale", "theme", "created_at", "details"}


class ImportFailure(ValueError):
    """Messages contain only fixed categories, never source field values."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ImportFailure("Duplicate JSON key.")
        result[key] = value
    return result


def parse_export(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ImportFailure("Import file exceeds the size limit.")
    try:
        payload = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ImportFailure("Invalid import JSON.") from None
    if (type(payload) is not dict or set(payload) != {"format", "source", "users"}
            or type(payload['format']) is not int or payload['format'] not in (1, 2)
            or not isinstance(payload['source'], str)
            or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', payload['source'])
            or type(payload['users']) is not list or len(payload['users']) > MAX_USERS):
        raise ImportFailure("Invalid import envelope.")
    ids = set()
    for row in payload['users']:
        if (type(row) is not dict or set(row) != (FIELDS | {'activation_pending'} if payload['format'] == 2 else FIELDS)
                or type(row['id']) is not int or not 1 <= row['id'] < 2**63 or row['id'] in ids
                or type(row['deleted']) is not bool):
            raise ImportFailure("Invalid or duplicate source identity.")
        ids.add(row['id'])
    return payload


def compatible_hash(value):
    if not isinstance(value, str) or len(value) > 512:
        return False
    # Exact algorithms and bounded work prevent attacker-controlled KDF costs.
    return bool(re.fullmatch(r'scrypt:32768:8:1\$[a-zA-Z0-9]{1,64}\$[0-9a-f]{128}', value)
                or re.fullmatch(r'pbkdf2:sha256:(?:[1-9][0-9]{0,5}|1000000)\$[a-zA-Z0-9]{1,64}\$[0-9a-f]{64}', value))


def _values(row, format_version=1):
    role_map = ROLE_MAP if format_version == 1 else {'user': 'user', 'staff': 'staff', 'admin': 'admin'}
    if format_version == 2 and type(row['activation_pending']) is not bool:
        raise ImportFailure('Invalid account fields.')
    if (type(row['active']) is not bool or row['role'] not in role_map
            or row['locale'] not in ('en', 'de', 'fr') or row['theme'] not in ('system', 'dark', 'light')
            or type(row['created_at']) is not int or not 0 <= row['created_at'] <= 253402300799
            or type(row['details']) is not dict or set(row['details']) != set(DETAIL_FIELDS)
            or not isinstance(row['email'], str) or not isinstance(row['display_name'], str)
            or not isinstance(row['password_hash'], str) or len(row['password_hash']) > 512):
        raise ImportFailure("Invalid account fields.")
    try:
        values = dict(validate_details(row['details']), email=normalize_email(row['email']),
            display_name=validate_name(row['display_name']), role=role_map[row['role']],
            active=row['active'], created_at=row['created_at'], locale=row['locale'], theme=row['theme'],
            activation_pending=row.get('activation_pending', False), password_hash=row['password_hash'])
    except (ValueError, TypeError, AttributeError):
        raise ImportFailure("Invalid account fields.") from None
    if not compatible_hash(row['password_hash']):
        values.update(active=False, activation_pending=True, password_hash=None)
    return values


def _target_digest(row):
    return digest({key: row[key] for key in users.c.keys() if key != 'id'})


def _plan(app, conn, payload):
    current = {r['id']: dict(r) for r in conn.execute(select(users).order_by(users.c.id)).mappings()}
    imported = {(r['source'], r['source_id']): dict(r) for r in conn.execute(select(links).order_by(links.c.source, links.c.source_id)).mappings()}
    choices = [dict(r) for r in conn.execute(select(options).order_by(options.c.id)).mappings()]
    # HMAC binds source and all relevant target data, without publishing password hashes.
    state = digest([payload, list(current.values()), list(imported.values()), choices])
    token = hmac.new(app.config['SECRET_KEY'].encode(), state.encode(), hashlib.sha256).hexdigest()
    emails = {r['email']: uid for uid, r in current.items()}
    source_emails = set()
    rows, writes = [], []
    for row in payload['users']:
        entry = {'source_id': row['id'], 'action': 'conflict', 'reason': '', 'user_id': None}
        rows.append(entry)
        link = imported.get((payload['source'], row['id']))
        if row['deleted']:
            entry.update(action='conflict' if link else 'skip', reason='source_deleted')
            continue
        try:
            value = _values(row, payload['format'])
        except (ImportFailure, TypeError):
            entry['reason'] = 'invalid_fields'
            continue
        entry.update(email=value['email'], role=value['role'], active=value['active'], reset_required=value['activation_pending'])
        if value['email'] in source_emails:
            entry['reason'] = 'duplicate_email'
            continue
        source_emails.add(value['email'])
        if link and link['user_id'] not in current:
            entry['reason'] = 'target_deleted' if link['user_id'] is None else 'missing_target'
            continue
        old = current.get(link['user_id']) if link else None
        entry['user_id'] = old['id'] if old else None
        if value['email'] in emails and (not old or emails[value['email']] != old['id']):
            entry['reason'] = 'email_collision'
            continue
        source_digest = digest(row)
        if old and link['source_digest'] == source_digest:
            entry.update(action='unchanged', reason='source_unchanged')
            continue
        if old and link['target_digest'] != _target_digest(old):
            entry['reason'] = 'local_changes'
            continue
        try:
            validate_choices(conn, value, old)
        except ValueError:
            entry['reason'] = 'unknown_option'
            continue
        entry.update(action='update' if old else 'create', reason='reset_required' if value['activation_pending'] else 'ready')
        writes.append((entry, value, source_digest))
    # Simultaneous demotions must not remove the last usable administrator.
    after = {uid: r for uid, r in current.items()}
    for entry, value, _source_digest in writes:
        after[entry['user_id'] or -entry['source_id']] = value
    if any(r['role'] == 'admin' and r['active'] and not r['activation_pending'] for r in current.values()) and not any(
            r['role'] == 'admin' and r['active'] and not r['activation_pending'] for r in after.values()):
        rows.append({'source_id': None, 'user_id': None, 'action': 'conflict', 'reason': 'last_admin'})
    report = {'source': payload['source'], 'plan': token, 'applied': False, 'rows': rows,
              'blocked': any(r['reason'] == 'last_admin' for r in rows),
              'counts': {action: sum(r['action'] == action for r in rows) for action in ('create', 'update', 'unchanged', 'skip', 'conflict')}}
    return report, writes


def preview(app, raw, *, actor_id=None, operator=False):
    payload = parse_export(raw)
    with app.extensions['neofab2_db'].connect() as conn:
        # Explicit read snapshot; no schema or import/audit mutation.
        conn.exec_driver_sql('BEGIN')
        if not operator:
            require_actor(conn, actor_id)
        report, _writes = _plan(app, conn, payload)
        return report


def apply_import(app, raw, expected_plan, *, actor_id=None, operator=False, skip_conflicts=False):
    payload = parse_export(raw)
    with write_transaction(app) as conn:
        if not operator:
            require_actor(conn, actor_id)
        report, writes = _plan(app, conn, payload)
        if (not isinstance(expected_plan, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_plan)
                or not hmac.compare_digest(report['plan'], expected_plan)):
            raise ImportFailure('Import preview is stale. Create a new preview.')
        if report['blocked'] or (report['counts']['conflict'] and skip_conflicts is not True):
            raise ImportFailure('Import has conflicts. No accounts were changed.')
        for entry, value, source_digest in writes:
            if value['password_hash'] is None:
                value['password_hash'] = hash_password(secrets.token_urlsafe(48))
            uid = entry['user_id']
            if uid is None:
                from .users import reserve_user_id
                uid = conn.execute(users.insert().values(id=reserve_user_id(conn), **value)).inserted_primary_key[0]
                entry['user_id'] = uid
                conn.execute(links.insert().values(source=payload['source'], source_id=entry['source_id'],
                    user_id=uid, source_digest=source_digest, target_digest=_target_digest(value)))
            else:
                conn.execute(update(users).where(users.c.id == uid).values(**value))
                conn.execute(update(links).where(links.c.source == payload['source'], links.c.source_id == entry['source_id']).values(
                    source_digest=source_digest, target_digest=_target_digest(value)))
                conn.execute(delete(sessions).where(sessions.c.user_id == uid))
                from .account_flows import invalidate_tokens
                invalidate_tokens(conn, uid)
            record(conn, 'user.imported', actor_id=actor_id, target_id=uid)
        report['applied'] = True
        return report
