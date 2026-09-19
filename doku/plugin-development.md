# Plugin-Vertrag und Backend-Verwaltung – API 1, Core 0.1.5

Dieses Arbeitspaket setzt N01 sowie Teile von S01, S12 und U06 um. Es enthält
zwei synthetische Testplugins, keine produktiven Fachplugins.

## Zielbild für die nächsten Plugin-Schritte

Vor Fachplugin-Arbeiten den [Plugin-Umsetzungsplan](Plugin_Umsetzungsplan.md) lesen.
Erstes Referenzplugin wird `printing3d` nach vollständiger Core-Abnahme und
minimaler `orders`-Basis. Zunächst den Vertrag für mehrere Rechte und
Besitzerprüfung mit Testplugins ausbauen. `employee` aus der Planung entspricht
dem vorhandenen `staff`; API 1 implementiert diese feineren Rechte noch nicht.
Datei-Upload und STL-/3D-Viewer sind interne gemeinsame Komponenten. Der MVP
bleibt ohne PrintFleet; Slicing erfolgt extern. PrintFleet-Anschluss und
weitere Viewer-/Dateiformate sind separat zu spezifizieren.

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
Templates können das gemeinsame `base.html` erweitern. Die Testplugins kapseln
ihre Vorlagen unter `plugins/templates/core_test/` und
`plugins/templates/management_test/`; die Paketierung nimmt sie ausdrücklich mit auf.

`Dependency(kennung, minimum_version)` verlangt ein installiertes und aktiviertes
Plugin ab der angegebenen Version. Die Untergrenze ist inklusive, ohne implizite
Major-Obergrenze. Abhängigkeiten starten vor ihren Nutzern. Fehlende oder zu alte
Abhängigkeiten, Zyklen, doppelte Kennungen und inkompatible aktive API-Versionen
brechen den Start verständlich ab. Es gibt keine automatische Aktivierung.

Der feste Katalog `builtin_plugins()` enthält ausschließlich geprüften,
mitgelieferten Code. Keine Importpfade aus TOML, kein Upload und kein Nachladen.
Plugins sind vertrauenswürdiger Python-Code, keine Sandbox. Core-Benutzertabellen
und Core-Routen importieren keine Plugin-Implementierungen.

## Backend-Verwaltung und manueller Neustart

Nach dem regulären Update auf 0.1.5 als **NeoFab2-Administrator** anmelden und
**Plugins** (`/admin/plugins`) öffnen. Das zusätzliche Recht `core.plugins.manage`
erlaubt ausschließlich Administratoren Änderungen; POST-Formulare sind CSRF-geschützt.

Die Übersicht unterscheidet **Im laufenden Webprozess** und **Gespeicherte Auswahl**.
**Aktivierung vormerken** bzw. **Deaktivierung vormerken** speichert die Auswahl
für den nächsten Start. Bei Abweichung erscheint **Neustart erforderlich**.
Bis zum Neustart laufen die bisherigen Seiten und Aufgaben weiter. Die Seite
führt keinen Neustart aus und besitzt keine Proxmox-Zugangsdaten.

Der **Proxmox-Admin** startet den betreffenden NeoFab2-Container in der
Proxmox-Oberfläche manuell neu. Damit werden alle Web- und Aufgabenprozesse
neu gestartet. Anschließend die Plugin-Übersicht neu laden; gespeicherte und
laufende Auswahl müssen übereinstimmen. Ein einzelner neuer Worker oder eine
frisch gestartete CLI übernimmt die Auswahl bereits beim eigenen Start;
die Anzeige beschreibt deshalb ausdrücklich den antwortenden Webprozess.
Sie bestätigt nicht den Zustand aller anderen Prozesse.

Alternativ kann ein berechtigter **root im Container** sämtliche derzeitigen
Webprozesse mit `systemctl restart neofab2.service` neu starten. Falls künftig
separate Aufgabenprozesse laufen, müssen auch diese neu gestartet werden.
Der vollständige manuelle Container-Neustart bleibt der einfache Betriebsweg.

## Zwei Testplugins prüfen

| Plugin | Version / API | Abhängigkeit | Zweck |
|---|---|---|---|
| Core-Testplugin (`core_test`) | 0.1.0 / 1 | keine | einfache Seite und lokale Testaufgabe |
| Verwaltungs-Testplugin (`management_test`) | 0.1.0 / 1 | `core_test` ab 0.1.0 | Abhängigkeitsprüfung, zweite Seite und geschützter Formularaufruf |

1. Zunächst beim Core-Testplugin **Aktivierung vormerken** wählen, sofern es noch
   nicht ausgewählt ist. Danach das Verwaltungs-Testplugin vormerken. Es reicht,
   beide Auswahlen vor demselben Neustart zu speichern.
2. Vor dem Neustart bleiben neu aktivierte Seiten unzugänglich. Den Proxmox-Admin
   um den manuellen Container-Neustart bitten.
3. Nach dem Neustart erscheinen beide Menüpunkte für Administratoren.
   `/plugins/management_test/` öffnen und **Formularzugriff testen** betätigen.
   Erwartet: `Verwaltungstest erfolgreich: Geschützter Formularaufruf ausgeführt.`
   Es werden keine Fachdaten angelegt.
4. Solange das Verwaltungs-Testplugin in der gespeicherten Auswahl aktiv ist,
   darf das Core-Testplugin nicht deaktiviert werden. Der Versuch muss eine
   Abhängigkeitsmeldung liefern und die bisherige Auswahl erhalten.
5. Erst das Verwaltungs-Testplugin, dann das Core-Testplugin deaktivieren lassen.
   Nach dem nächsten manuellen Neustart fehlen ihre Menüpunkte und direkte
   Seitenaufrufe liefern 404. Lokale Aufgaben werden mit Exit-Code 1 abgewiesen.

Benutzer und Mitarbeiter dürfen weder die Plugin-Verwaltung noch aktivierte
Testseiten nutzen (403); ohne Anmeldung folgt die Weiterleitung zum Login.
Eine noch ausstehende Änderung kann durch Vormerken des bisherigen Zustands
wieder aufgehoben werden. Stimmen beide Zustände überein, ist dafür kein Neustart nötig.

Nach erfolgter Aktivierung eine lokale Aufgabe als **root im Container**,
ausgeführt mit dem Dienstbenutzer, prüfen:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 plugin-task management_test self_check
```

Erwartet: `Management test plugin: task completed successfully.` Dieser lokale
Betriebszugang verwendet keine Browserrolle; Zugriff auf Dienstkonto und
Konfiguration ist seine Berechtigungsgrenze. Aufgaben sind benannte Callables ohne
Parameter. Es gibt noch keine Warteschlange, Fälligkeitsplanung oder automatischen Jobs.

## Speicherung und Übernahme von 0.1.4

Die Auswahl liegt als JSON unter `core.plugins.enabled` in der vorhandenen
Tabelle `core_settings` und wird mit der Datenbanksicherung gesichert. Keine
neue Schema-Revision. Änderungen erfolgen atomar und jeweils gegen den neuesten
DB-Stand; Rechte werden innerhalb derselben Transaktion erneut geprüft.
Es werden keine Plugins deinstalliert und keine Plugin-Daten gelöscht.

Solange kein Backend-Zustand gespeichert ist, gilt weiterhin `ENABLED_PLUGINS`
aus `/etc/neofab2/config.toml`, standardmäßig `[]`. Damit bleibt eine bestehende
Testplugin-Aktivierung beim Update erhalten. Ab dem ersten erfolgreichen
Backend-Speichern hat die Datenbank Vorrang, auch bei einer leeren Auswahl.
Eine spätere Änderung von TOML allein überschreibt sie nicht. Serverstart und
Seitenaufrufe legen keinen Auswahl-Datensatz und kein Schema automatisch an.

## Lokale Wiederherstellung

Falls die gespeicherte Auswahl nach einer manuellen Datenänderung oder einem
inkompatiblen Plugin-Paket ungültig ist, bricht der Start ab. Für die lokale
Wiederherstellung als **root im Container** eine gültige Ausgangsliste in
`/etc/neofab2/config.toml` setzen, z. B. den vorhandenen Eintrag ersetzen durch:

```toml
ENABLED_PLUGINS = []
```

Dann ausdrücklich die Konfigurationsauswahl übernehmen:

```bash
cd /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 plugins-restore-config
```

Der Befehl fragt nach Bestätigung und validiert die Konfigurationsauswahl. Er
ersetzt nur den gespeicherten Plugin-Zielzustand; andere Einstellungen und Daten
bleiben erhalten. Danach den Container durch den Proxmox-Admin neu starten lassen.
Erwartet: Core startet mit der gewählten Ausgangsliste; Plugins können anschließend
wieder im Backend ausgewählt werden. Secrets und Cookie-Einstellungen beibehalten.

## Fehlerhilfe und Grenzen

Bei `Plugin nicht installiert`, `benötigt` oder `Inkompatible Plugin-API`
Kennungen, Versionen und gespeicherte Aktivierungsliste korrigieren, danach
`check` wiederholen. Bei nicht startendem Backend die lokale Wiederherstellung
verwenden. Fehlgeschlagene Prüfung nicht durch Deaktivieren von
Sicherheitsprüfungen umgehen. Bei Dienststartfehlern `journalctl -u neofab2.service
-n 80 --no-pager` lokal prüfen.

Das Plugin-Grundsystem in 0.1.3 benötigte keine neue Datenbankrevision.
Core 0.1.4 ergänzt `0003_user_theme`; 0.1.5 ergänzt keine neue Revision.
Beide Testplugins haben weiterhin keine Tabellen.
Künftige Plugin-Schemata benötigen explizite versionierte Migrationen in der
zentralen Migrationenkette. Plugin-Einstellungen, Benachrichtigungs-/Dateidienste,
persistente Aufgaben und feinere Rechte
sind noch nicht Teil von API 1. Die vollständige Core-Abnahme steht aus.

Ab 0.1.7 sind Plugin-Namen, Testseiten und CLI-Meldungen im Quelltext englisch.
Die Oberfläche verwendet englische Übersetzungsschlüssel und Englisch als Fallback.
Die zentrale Core-Version ist 0.1.9; Testplugin-Versionen bleiben 0.1.0, API bleibt 1.

Für Plugin-Oberflächen gelten die [UI-Gestaltungsregeln](UI_Gestaltungsregeln.md).
Alle Buttons enthalten sichtbaren übersetzbaren Text und ein passendes Icon aus
`ui_icons.html`; Templates mit `base.html` können das gemeinsame `icon()` verwenden.
