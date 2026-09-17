"""Validierter, pro Prozess unveränderlicher Aktivierungsstand."""

import re
from types import MappingProxyType

from . import API_VERSION


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value):
        raise ValueError("Plugin-Version muss MAJOR.MINOR.PATCH sein.")
    return tuple(map(int, value.split(".")))


class Registry:
    def __init__(self, plugins, enabled):
        available = {}
        for plugin in plugins:
            key = plugin.plugin_id
            if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key == "core":
                raise ValueError("Ungültige Plugin-Kennung.")
            if key in available:
                raise ValueError(f"Doppelte Plugin-Kennung: {key}")
            version_tuple(plugin.version)
            if (not plugin.name or plugin.permission != f"{key}.access"
                    or not plugin.roles or not set(plugin.roles) <= {"user", "staff", "admin"}
                    or not callable(plugin.blueprint_factory)):
                raise ValueError(f"Ungültiger Plugin-Vertrag: {key}")
            task_names = set()
            for name, handler in plugin.tasks:
                if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name in task_names or not callable(handler):
                    raise ValueError(f"Ungültige Plugin-Aufgabe: {key}")
                task_names.add(name)
            dependency_names = set()
            for dependency in plugin.dependencies:
                version_tuple(dependency.minimum_version)
                if dependency.plugin_id in dependency_names:
                    raise ValueError(f"Doppelte Abhängigkeit: {key}")
                dependency_names.add(dependency.plugin_id)
            available[key] = plugin
        if not isinstance(enabled, list) or any(not isinstance(key, str) for key in enabled):
            raise ValueError("ENABLED_PLUGINS muss eine Liste von Plugin-Kennungen sein.")
        if len(set(enabled)) != len(enabled):
            raise ValueError("ENABLED_PLUGINS enthält doppelte Kennungen.")
        active = frozenset(enabled)
        ordered = []
        visiting = set()
        visited = set()

        def visit(key):
            if key not in available:
                raise ValueError(f"Plugin nicht installiert: {key}")
            if key in visiting:
                raise ValueError(f"Zyklische Plugin-Abhängigkeit: {key}")
            if key in visited:
                return
            plugin = available[key]
            if type(plugin.api_version) is not int or plugin.api_version != API_VERSION:
                raise ValueError(f"Inkompatible Plugin-API: {key}")
            visiting.add(key)
            for dependency in plugin.dependencies:
                dep = dependency.plugin_id
                if dep not in active:
                    raise ValueError(f"Plugin {key} benötigt aktiviertes Plugin {dep}.")
                visit(dep)
                if version_tuple(available[dep].version) < version_tuple(dependency.minimum_version):
                    raise ValueError(f"Plugin {key} benötigt {dep} ab {dependency.minimum_version}.")
            visiting.remove(key)
            visited.add(key)
            ordered.append(plugin)

        for key in enabled:
            visit(key)
        self.available = MappingProxyType(available)
        self.enabled = active
        self.ordered = tuple(ordered)

    def allows(self, user, permission):
        return bool(user and user["active"] and any(
            plugin.permission == permission and user["role"] in plugin.roles
            for plugin in self.ordered))

    def run_task(self, plugin_id, task_name):
        if plugin_id not in self.enabled:
            raise ValueError("Plugin ist nicht aktiv; Aufgabe nicht ausgeführt.")
        tasks = dict(self.available[plugin_id].tasks)
        if task_name not in tasks:
            raise ValueError("Unbekannte Plugin-Aufgabe.")
        return tasks[task_name]()
