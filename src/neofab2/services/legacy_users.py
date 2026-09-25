"""Read an operator-supplied SQLite snapshot; never import legacy Python code."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

from neofab2.core.user_import import MAX_BYTES, MAX_USERS, ImportFailure, parse_export
from neofab2.core.users import DETAIL_FIELDS


def export_snapshot(path, source):
    if not isinstance(source, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', source):
        raise ImportFailure('Invalid source identifier.')
    path = Path(path).resolve()
    required = {'id', 'email', 'password_hash', 'role', 'language', 'theme_mode', 'is_active', 'deleted_at', 'created_at', *DETAIL_FIELDS}
    try:
        if Path(str(path) + '-wal').exists():
            raise ImportFailure('Use a standalone SQLite backup without a WAL file.')
        with sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA trusted_schema=OFF')
            conn.execute('BEGIN')
            table = conn.execute("SELECT type, sql FROM sqlite_master WHERE name='user'").fetchone()
            if not table or table['type'] != 'table' or 'VIRTUAL' in table['sql'].upper():
                raise ImportFailure('Legacy user table is missing or unsupported.')
            columns = {r['name'] for r in conn.execute('PRAGMA table_info("user")')}
            if not required <= columns:
                raise ImportFailure('Legacy user columns are missing.')
            selected = ', '.join('"' + name + '"' for name in sorted(required))
            sizes = ' + '.join(f'coalesce(length("{name}"), 0)' for name in sorted(required))
            total = conn.execute(f'SELECT coalesce(sum({sizes}), 0) FROM "user"').fetchone()[0]
            if total > MAX_BYTES:
                raise ImportFailure('Legacy account data exceeds the size limit.')
            rows = conn.execute(f'SELECT {selected} FROM "user" ORDER BY id LIMIT ?', (MAX_USERS + 1,)).fetchall()
            if len(rows) > MAX_USERS:
                raise ImportFailure('Too many source users.')
            result = []
            for row in rows:
                if row['deleted_at'] is not None:
                    # Deleted source rows contribute only their stable identity.
                    result.append(dict(id=row['id'], deleted=True, email='', display_name='', role='user',
                        active=False, password_hash='', locale='en', theme='system', created_at=0,
                        details={name: '' for name in DETAIL_FIELDS}))
                    continue
                if type(row['is_active']) is not int or row['is_active'] not in (0, 1):
                    raise ImportFailure('Invalid legacy account status.')
                created = datetime.fromisoformat(row['created_at'])
                # NeoFab stores naive UTC datetimes; offset-bearing exports normalize to UTC.
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                details = {name: row[name] or '' for name in DETAIL_FIELDS}
                name = ' '.join(part.strip() for part in (details['first_name'], details['last_name']) if part.strip())
                result.append(dict(id=row['id'], deleted=False, email=row['email'],
                    display_name=name or row['email'].split('@')[0], role=row['role'],
                    active=bool(row['is_active']), password_hash=row['password_hash'],
                    locale=row['language'], theme=row['theme_mode'], created_at=int(created.timestamp()), details=details))
        raw = json.dumps({'format': 1, 'source': source, 'users': result}, ensure_ascii=True, indent=2).encode()
        if len(raw) > MAX_BYTES:
            raise ImportFailure('Import file exceeds the size limit.')
        parse_export(raw)
        return raw
    except (sqlite3.Error, OSError, ValueError, TypeError, AttributeError, OverflowError):
        raise ImportFailure('Cannot export legacy snapshot; check schema, fields and file access.') from None
