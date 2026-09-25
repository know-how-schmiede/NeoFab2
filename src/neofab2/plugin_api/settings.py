"""API 1: declared non-secret plugin settings in authenticated requests."""


def read_settings(plugin_id, *, connection=None):
    from neofab2.services.plugin_settings import read_settings as read
    return read(plugin_id, connection=connection)


def save_settings(plugin_id, values, *, connection=None):
    from neofab2.services.plugin_settings import save_settings as save
    return save(plugin_id, values, connection=connection)
