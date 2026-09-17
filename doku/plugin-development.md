# Plugin-Vertrag – API 1, Core 0.1.3

Dieses Arbeitspaket setzt N01 sowie Teile von S01, S12 und U06 um. Es enthält
nur ein synthetisches Testplugin, keine produktiven Fachplugins.

## Vertrag

`neofab2.plugin_api.Plugin` beschreibt Kennung, Anzeigename, eigene Version
im Format MAJOR.MINOR.PATCH, API-Version, Zugriffsrecht, erlaubte Core-Rollen,
Blueprint-Factory, Abhängigkeiten und optionale lokale Aufgaben.
API 1 unterstützt genau ein Zugriffsrecht je Plugin: `<kennung>.access`.
Die Rollen werden ausdrücklich angegeben; Administratoren erhalten keine
pauschalen Rechte für fremde Plugins. Weitere Einzelrechte und eigene Rollenpflege
bleiben einem späteren Vertragsausbau vorbehalten.

Die Factory erzeugt bei jedem App-Start einen neuen Flask-Blueprint namens
`plugin_<kennung>` mit einem GET-Endpunkt `index`. Der Core registriert ihn
unter `/plugins/<kennung>` und prüft Anmeldung und Recht vor seinen Hooks.
Schreibzugriffe behalten den zentralen CSRF-Schutz. Der Menüeintrag verweist
auf `index` und erscheint ausschließlich bei entsprechendem Recht.
Templates können das gemeinsame `base.html` erweitern. Das Testplugin kapselt
seine Vorlage unter `plugins/templates/core_test/index.html`; die Paketierung
nimmt sie ausdrücklich mit auf.

`Dependency(kennung, minimum_version)` verlangt ein installiertes und aktiviertes
Plugin ab der angegebenen Version. Die Untergrenze ist inklusive, ohne implizite
Major-Obergrenze. Abhängigkeiten starten vor ihren Nutzern. Fehlende oder zu alte
Abhängigkeiten, Zyklen, doppelte Kennungen und inkompatible aktive API-Versionen
brechen den Start verständlich ab. Es gibt keine automatische Aktivierung.

Der feste Katalog `builtin_plugins()` enthält ausschließlich geprüften,
mitgelieferten Code. Keine Importpfade aus TOML, kein Upload und kein Nachladen.
Plugins sind vertrauenswürdiger Python-Code, keine Sandbox. Core-Benutzertabellen
und Core-Routen importieren keine Plugin-Implementierungen.

## Test im Proxmox-Container

Nach dem regulären Update als **root** die Datei `/etc/neofab2/config.toml`
bearbeiten und diesen Eintrag auf oberster TOML-Ebene ergänzen bzw. ersetzen:

```toml
ENABLED_PLUGINS = ["core_test"]
```

Standard bei fehlendem Eintrag: `[]`, alle Plugins deaktiviert. Kein zweiter
gleichnamiger Eintrag. Bestehende Cookie-Einstellung und Secrets beibehalten.
Vor dem Neustart als root prüfen:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
systemctl restart neofab2.service
systemctl status neofab2.service --no-pager
```

Erwartet: erfolgreiche Bereitschaftsprüfung und aktiver Dienst. Als Administrator
anmelden: Unter **Plugins** (`/admin/plugins`) steht das Core-Testplugin als aktiv,
Version 0.1.0, API 1. Der Menüpunkt **Core-Testplugin** öffnet die Testseite.
Benutzer und Mitarbeiter erhalten bei direktem Zugriff HTTP 403; ohne Anmeldung
folgt die Weiterleitung zum Login.

Die synthetische Aufgabe als **root**, ausgeführt mit dem Dienstbenutzer:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 plugin-task core_test self_check
```

Erwartet: `Testplugin: Aufgabe erfolgreich ausgeführt.` Dieser lokale Betriebszugang
verwendet keine Browserrolle; Zugriff auf Dienstkonto und Konfiguration ist seine
Berechtigungsgrenze. Aufgaben sind benannte Callables ohne Parameter in API 1.
Es existieren noch keine Warteschlange, Fälligkeitsplanung oder automatischen Jobs.

Zur Deaktivierung den Eintrag auf `ENABLED_PLUGINS = []` setzen, `check` erneut
ausführen und den Dienst neu starten. Erwartet: Übersicht zeigt deaktiviert,
Menüeintrag entfällt, direkte Testseite liefert 404 und Aufgabe endet mit Exit-Code 1.
Konten, Sitzungen und Daten bleiben erhalten. Aktivierungsänderungen wirken erst
mit Neustart **aller** betroffenen Web-/Aufgabenprozesse, nicht während alter Prozesse.
Ein weiter aktives abhängiges Plugin verhindert den Start ohne seine Abhängigkeit.

## Fehlerhilfe und Grenzen

Bei `Plugin nicht installiert`, `benötigt` oder `Inkompatible Plugin-API`
Kennungen, Versionen und vollständige Aktivierungsliste korrigieren, danach
`check` wiederholen. Fehlgeschlagene Prüfung nicht durch Deaktivieren von
Sicherheitsprüfungen umgehen. Bei Dienststartfehlern `journalctl -u neofab2.service
-n 80 --no-pager` lokal prüfen.

Keine neue Datenbankrevision in 0.1.3. Das Testplugin hat keine Tabellen.
Künftige Plugin-Schemata benötigen explizite versionierte Migrationen in der
zentralen Migrationenkette. Plugin-Einstellungen, Benachrichtigungs-/Dateidienste,
persistente Aufgaben und feinere Rechte
sind noch nicht Teil von API 1. Die vollständige Core-Abnahme steht aus.
