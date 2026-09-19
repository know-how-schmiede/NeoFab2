"""Small, transactional file storage. No user-controlled filesystem paths."""

import secrets
import time
from pathlib import PurePosixPath

from flask import current_app, g
from sqlalchemy import Column, Integer, LargeBinary, MetaData, String, Table, select
from werkzeug.exceptions import NotFound, RequestEntityTooLarge
from werkzeug.utils import secure_filename

from neofab2.core.users import get_user, write_transaction
from neofab2.plugin_api import owns_or_allowed

files = Table("core_files", MetaData(),
    Column("id", String(32), primary_key=True), Column("plugin_id", String(80)),
    Column("owner_id", Integer), Column("filename", String(200)),
    Column("size", Integer), Column("created_at", Integer), Column("content", LargeBinary))


def context(connection, plugin_id):
    registry = current_app.extensions["neofab2_plugins"]
    if plugin_id not in registry.enabled or registry.available[plugin_id].files is None:
        raise NotFound()
    user = get_user(connection, g.current_user["id"]) if g.get("current_user") else None
    plugin = registry.available[plugin_id]
    if not registry.allows(user, plugin.permission):
        raise PermissionError()
    return user, plugin.files, registry


def store(plugin_id, upload):
    with write_transaction(current_app) as connection:
        user, policy, registry = context(connection, plugin_id)
        if not registry.allows(user, policy.upload):
            raise PermissionError()
        name = upload.filename if upload else ""
        if (not name or len(name) > 200 or any(c in name for c in '/\\:')
                or any(ord(c) < 32 or ord(c) == 127 for c in name)):
            raise ValueError("Please choose a file with a simple filename.")
        name = secure_filename(name)
        if not name or PurePosixPath(name).suffix.lower() not in policy.extensions:
            raise ValueError("This file type is not allowed.")
        content = upload.stream.read(policy.max_bytes + 1)
        if len(content) > policy.max_bytes:
            raise RequestEntityTooLarge()
        if not content:
            raise ValueError("Empty files are not allowed.")
        file_id = secrets.token_hex(16)
        connection.execute(files.insert().values(id=file_id, plugin_id=plugin_id,
            owner_id=user["id"], filename=name, size=len(content), created_at=int(time.time()), content=content))
        return file_id


def readable(plugin_id, file_id=None):
    with current_app.extensions["neofab2_db"].connect() as connection:
        user, policy, registry = context(connection, plugin_id)
        columns = list(files.c) if file_id is not None else [c for c in files.c if c.name != "content"]
        query = select(*columns).where(files.c.plugin_id == plugin_id)
        if file_id is not None:
            query = query.where(files.c.id == file_id)
        if not registry.allows(user, policy.read_all):
            if not registry.allows(user, policy.read_own):
                raise PermissionError()
            query = query.where(files.c.owner_id == user["id"])
        rows = list(connection.execute(query.order_by(files.c.created_at, files.c.id)).mappings())
        if file_id is not None:
            if not rows or not owns_or_allowed(user, rows[0]["owner_id"], policy.read_own, policy.read_all):
                raise NotFound()
            return rows[0]
        return rows
