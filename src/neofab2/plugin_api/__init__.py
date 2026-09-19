"""Öffentlicher Plugin-Vertrag, API-Version 1."""

from dataclasses import dataclass
from typing import Callable

API_VERSION = 1


@dataclass(frozen=True)
class Permission:
    name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class FilePolicy:
    upload: str
    read_own: str
    read_all: str
    max_bytes: int = 262144
    extensions: tuple[str, ...] = (".txt",)


@dataclass(frozen=True)
class Dependency:
    plugin_id: str
    minimum_version: str


@dataclass(frozen=True)
class Plugin:
    plugin_id: str
    name: str
    version: str
    api_version: int
    permission: str
    roles: tuple[str, ...]
    blueprint_factory: Callable
    dependencies: tuple[Dependency, ...] = ()
    # Aufgaben laufen ausdrücklich per Betriebs-CLI, noch kein Scheduler.
    tasks: tuple[tuple[str, Callable], ...] = ()
    permissions: tuple[Permission, ...] = ()
    files: FilePolicy | None = None


def has_permission(user, permission):
    from neofab2.core.users import has_permission as check
    return check(user, permission)


def owns_or_allowed(user, owner_id, own_permission, all_permission):
    """An explicit broad permission or ownership AND an explicit own permission."""
    return bool(user and user["active"] and (
        has_permission(user, all_permission) or
        (user["id"] == owner_id and has_permission(user, own_permission))))


def permission_required(permission):
    from neofab2.core.auth import permission_required as guard
    return guard(permission)


def builtin_plugins():
    """Fester Lieferumfang; kein Importpfad oder Code-Upload aus Konfiguration."""
    from neofab2.plugins.core_test import plugin
    from neofab2.plugins.management_test import plugin as management_plugin
    return (plugin, management_plugin)
