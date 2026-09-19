"""Validierter, pro Prozess unveränderlicher Aktivierungsstand."""

import re
from types import MappingProxyType

from . import API_VERSION


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value):
        raise ValueError("Plugin version must use MAJOR.MINOR.PATCH.")
    return tuple(map(int, value.split(".")))


class Registry:
    def __init__(self, plugins, enabled):
        available = {}
        for plugin in plugins:
            key = plugin.plugin_id
            if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key == "core":
                raise ValueError("Invalid plugin ID.")
            if key in available:
                raise ValueError(f"Duplicate plugin ID: {key}")
            version_tuple(plugin.version)
            if (not plugin.name or plugin.permission != f"{key}.access"
                    or not plugin.roles or not set(plugin.roles) <= {"user", "staff", "admin"}
                    or not callable(plugin.blueprint_factory)):
                raise ValueError(f"Invalid plugin contract: {key}")
            names = {plugin.permission}
            for permission in plugin.permissions:
                if (not isinstance(permission.name, str)
                        or not re.fullmatch(re.escape(key) + r"\.[a-z][a-z0-9_]*", permission.name)
                        or permission.name in names or not permission.roles
                        or not set(permission.roles) <= {"user", "staff", "admin"}):
                    raise ValueError(f"Invalid plugin permission contract: {key}")
                names.add(permission.name)
            policy = plugin.files
            if policy is not None and (
                    not {policy.upload, policy.read_own, policy.read_all} <= names
                    or len({policy.upload, policy.read_own, policy.read_all}) != 3
                    or type(policy.max_bytes) is not int or not 1 <= policy.max_bytes <= 1048576
                    or not policy.extensions or any(
                        not isinstance(ext, str) or not re.fullmatch(r"\.[a-z0-9]+", ext)
                        for ext in policy.extensions)):
                raise ValueError(f"Invalid plugin file contract: {key}")
            task_names = set()
            for name, handler in plugin.tasks:
                if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name in task_names or not callable(handler):
                    raise ValueError(f"Invalid plugin task: {key}")
                task_names.add(name)
            dependency_names = set()
            for dependency in plugin.dependencies:
                version_tuple(dependency.minimum_version)
                if dependency.plugin_id in dependency_names:
                    raise ValueError(f"Duplicate dependency: {key}")
                dependency_names.add(dependency.plugin_id)
            available[key] = plugin
        if not isinstance(enabled, list) or any(not isinstance(key, str) for key in enabled):
            raise ValueError("ENABLED_PLUGINS must be a list of plugin IDs.")
        if len(set(enabled)) != len(enabled):
            raise ValueError("ENABLED_PLUGINS contains duplicate IDs.")
        active = frozenset(enabled)
        ordered = []
        visiting = set()
        visited = set()

        def visit(key):
            if key not in available:
                raise ValueError(f"Plugin not installed: {key}")
            if key in visiting:
                raise ValueError(f"Cyclic plugin dependency: {key}")
            if key in visited:
                return
            plugin = available[key]
            if type(plugin.api_version) is not int or plugin.api_version != API_VERSION:
                raise ValueError(f"Incompatible plugin API: {key}")
            visiting.add(key)
            for dependency in plugin.dependencies:
                dep = dependency.plugin_id
                if dep not in active:
                    raise ValueError(f"Plugin {key} requires enabled plugin {dep}.")
                visit(dep)
                if version_tuple(available[dep].version) < version_tuple(dependency.minimum_version):
                    raise ValueError(f"Plugin {key} requires {dep} version {dependency.minimum_version} or later.")
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
            ((plugin.permission == permission and user["role"] in plugin.roles)
             or any(item.name == permission and user["role"] in item.roles
                    for item in plugin.permissions))
            for plugin in self.ordered))

    def run_task(self, plugin_id, task_name):
        if plugin_id not in self.enabled:
            raise ValueError("Plugin is not active; task was not executed.")
        tasks = dict(self.available[plugin_id].tasks)
        if task_name not in tasks:
            raise ValueError("Unknown plugin task.")
        return tasks[task_name]()
