"""API 1: isolated plugin catalogs with English source text and fallback."""
from string import Formatter
from types import MappingProxyType
from flask import current_app
from neofab2.core.i18n import current_language


def fields(message):
    result = set()
    for _, name, spec, conversion in Formatter().parse(message):
        if name is not None:
            if not name.isidentifier() or spec or conversion:
                raise ValueError("Use named translation placeholders without formatting.")
            result.add(name)
    return result


def freeze_catalog(catalog):
    if not isinstance(catalog, dict):
        raise ValueError("Invalid plugin translations.")
    result = {}
    for language, messages in catalog.items():
        if language not in {"de", "fr"} or not isinstance(messages, dict):
            raise ValueError("Invalid plugin translation language.")
        translated = {}
        for source, target in messages.items():
            if not isinstance(source, str) or not isinstance(target, str) or not source or not target:
                raise ValueError("Invalid plugin translation text.")
            if fields(source) != fields(target):
                raise ValueError("Plugin translation placeholders differ.")
            translated[source] = str(target)
        result[language] = MappingProxyType(translated)
    return MappingProxyType(result)


def translate(plugin_id, message, **values):
    registry = current_app.extensions["neofab2_plugins"]
    if plugin_id not in registry.enabled:
        raise ValueError("Plugin is not active.")
    result = registry.translations[plugin_id].get(current_language(), {}).get(message, message)
    return str(result).format(**values) if values else str(result)
