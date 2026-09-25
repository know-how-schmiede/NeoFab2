"""API 1 additive small-file contract; requires an authenticated request."""

from io import BytesIO
from flask import send_file


def store_file(plugin_id, upload, *, connection=None):
    from neofab2.services.files import store
    return store(plugin_id, upload, connection=connection)


def list_files(plugin_id):
    from neofab2.services.files import readable
    return readable(plugin_id)


def download_file(plugin_id, file_id):
    from neofab2.services.files import readable
    record = readable(plugin_id, file_id)
    return send_file(BytesIO(record["content"]), mimetype="application/octet-stream",
                     as_attachment=True, download_name=record["filename"], max_age=0)
