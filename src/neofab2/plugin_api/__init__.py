"""Öffentlicher Plugin-Vertrag, API-Version 1."""

from dataclasses import dataclass
from typing import Callable

API_VERSION = 1


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


def builtin_plugins():
    """Fester Lieferumfang; kein Importpfad oder Code-Upload aus Konfiguration."""
    from neofab2.plugins.core_test import plugin
    return (plugin,)
