# Plugin-Vertrag und Backend-Verwaltung – API 1, Core 0.1.13

Dieses Arbeitspaket setzt N01 sowie Teile von S01, S12 und U06 um. Es enthält
drei technische Testplugins, keine produktiven Fachplugins.

**Geplanter Ausbau, noch nicht verfügbar:** [Plugin-Pakete und Lifecycle](Plugin_Pakete_und_Lifecycle.md)
legt eigene Verzeichnisse samt Ressourcen, Mindestzugriff per Admin-Auswahl,
kontrollierten ZIP-Import und Deinstallation mit Datenerhalt fest. Die folgenden
Abschnitte beschreiben weiterhin den implementierten API-1-Stand: feste Rollen,
mitgelieferter Katalog, kein ZIP-Installer. Die neuen Schritte stehen im
[Core-Arbeitsplan](Core_Naechste_Schritte.md).

## Zielbild für die nächsten Plugin-Schritte

Vor Fachplugin-Arbeiten den [Plugin-Umsetzungsplan](Plugin_Umsetzungsplan.md) lesen.
Erstes Referenzplugin wird `printing3d` nach vollständiger Core-Abnahme und
minimaler `orders`-Basis. Mehrere Rechte und Besitzerprüfung sind seit 0.1.10
mit Testplugins umgesetzt. `employee` aus der Planung entspricht
dem vorhandenen `staff`. [Dateivertrag und Rechte](Core_Dateien_und_Rechte.md).
Datei-Upload und STL-/3D-Viewer sind interne gemeinsame Komponenten. Der MVP
bleibt ohne PrintFleet; Slicing erfolgt extern. PrintFleet-Anschluss und
weitere Viewer-/Dateiformate sind separat zu spezifizieren.

## Vertrag

`neofab2.plugin_api.Plugin` beschreibt Kennung, Anzeigename, eigene Version
im Format MAJOR.MINOR.PATCH, API-Version, Zugriffsrecht, erlaubte Core-Rollen,
Blueprint-Factory, Abhängigkeiten und optionale lokale Aufgaben.
API 1 unterstützt das Einstiegsrecht `<kennung>.access` und seit 0.1.10
optionale zusätzliche `Permission`-Deklarationen sowie `FilePolicy`.
Die Rollen werden ausdrücklich angegeben; Administratoren erhalten keine
pauschalen Rechte für fremde Plugins. Eigene Rollenpflege bleibt offen.

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

Nach dem regulären Update als **NeoFab2-Administrator** anmelden und
**Administration → Plugins** (`/admin/plugins`) öffnen. Das zusätzliche Recht `core.plugins.manage`
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

## Technische Testplugins prüfen

| Plugin | Version / API | Abhängigkeit | Zweck |
|---|---|---|---|
| Core-Testplugin (`core_test`) | 0.1.0 / 1 | keine | einfache Seite und lokale Testaufgabe |
| Verwaltungs-Testplugin (`management_test`) | 0.1.0 / 1 | `core_test` ab 0.1.0 | Abhängigkeiten, mehrere Rechte, Besitzerprüfung, geschütztes Formular und Testdateien |
| CheckDesign (`checkdesign`) | 0.1.0 / 1 | keine | Galerie aller vorhandenen Designelemente für Mitarbeiter/Admins mit lokaler Hell-/Dunkel-Vorschau |

CheckDesign wird unabhängig aktiviert und besitzt keine Schreibfunktionen.
[Aktivierung und Bedienung](CheckDesign.md). Die folgende Abhängigkeitsprüfung
betrifft weiterhin die ersten beiden Testplugins.

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

Benutzer und Mitarbeiter dürfen die Plugin-Verwaltung und die `core_test`-Seite
nicht nutzen (403). Seit 0.1.10 ist `management_test` für alle drei Rollen
zugänglich: Benutzer sehen eigene Dateien; Mitarbeiter und Administratoren alle
Dateien dieses Testplugins. Die Formularprüfung erfordert Mitarbeiter-/Adminrecht.
Ohne Anmeldung folgt die Weiterleitung zum Login.
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
zentralen Migrationenkette. Seit 0.1.10 hält `core_files` über Revision
`0008_core_files` Testdateien im technischen Core-Dienst. Mehrere Rechte und der
minimale Dateivertrag sind Teil von API 1. Plugin-Einstellungen sind seit
0.1.17 verfügbar, Benachrichtigungen und persistente Versandaufträge seit 0.1.12.
Ein allgemeiner persistenter Aufgabenplaner bleibt offen.
Die vollständige Core-Abnahme steht aus.

Ab 0.1.7 sind Plugin-Namen, Testseiten und CLI-Meldungen im Quelltext englisch.
Die Oberfläche verwendet englische Übersetzungsschlüssel und Englisch als Fallback.
Die zentrale Core-Version ist 0.1.17; Testplugin-Versionen bleiben 0.1.0, API bleibt 1.

Seit 0.1.12 ergänzt `mail_permission` den Vertrag optional. Es muss auf ein
explizites zusätzliches Plugin-Recht verweisen. `plugin_api/notifications.py`
stellt `enqueue_email()` für authentifizierte Requests bereit: frischer
Kontostand, Einstieg und Versandrecht, dauerhafte Idempotenz sowie optional
gemeinsame Transaktion mit dem Aufrufer. Deaktivierte Plugin-Aufträge bleiben
gespeichert, werden aber nicht übernommen. Kein direkter SMTP-Aufruf aus Plugins.
[Vertragsbeispiel, Worker, Zustände und Grenzen](Core_SMTP_und_Versand.md).

Für Plugin-Oberflächen gelten die [UI-Gestaltungsregeln](UI_Gestaltungsregeln.md).
Alle Buttons enthalten sichtbaren übersetzbaren Text und ein passendes Icon aus
`ui_icons.html`; Templates mit `base.html` können das gemeinsame `icon()` verwenden.

## Audit-Vertrag ab Core 0.1.15 (API 1)

`neofab2.plugin_api.audit.record_action(plugin_id, permission, target_id=None, connection=None)`
protokolliert eine deklarierte Aktion nach aktueller Konto-, Einstiegs- und
Aktionsrechteprüfung. Nur numerische Objekt-ID, kein Freitext oder Secret-Payload.
Mit übergebener aktiver NeoFab2-Verbindung atomar zur Fachaktion; Objektberechtigung
bleibt Aufgabe des Plugins. Administratoren erhalten keinen Wildcard-Zugriff.
[Schnittstelle, Beispiel und Grenzen](Core_Audit_und_Betriebsstatus.md).

## Übersetzungen (API 1, ab Core 0.1.16)

Optionales `Plugin.translations`: `{"de": {englischer_text: übersetzung},
"fr": {...}}`. Die Registry validiert die Sprachen und übernimmt eine unveränderliche
Kopie; Kataloge sind je Plugin getrennt. Fehlende Texte fallen auf den englischen
Quelltext zurück. Platzhalter müssen gleich sein; nur `{name}` ohne Attributzugriff,
Formatangaben oder Konvertierung ist zulässig. HTML bleibt in Jinja escaped.

```python
from neofab2.plugin_api.i18n import translate
message = translate("core_test", "Hello {name}", name="Synthetic")
```

Im Template: `{{ plugin_translate("core_test", "Hello {name}", name="Synthetic") }}`.
Ein App-Kontext ist erforderlich; außerhalb einer Anfrage ist die Sprache Englisch.
Unbekannte oder nicht geladene Plugins werden abgewiesen. Die Übersetzung selbst
vergibt keine Zugriffsrechte; bestehende Blueprint-/Aktionssperren gelten weiter.
`core_test` liefert einen deutschen/französischen Vertragsnachweis. Keine API- oder
Testplugin-Versionsanhebung, da das neue Feld optional und rückwärtskompatibel ist.

## Einstellungen, Dateitransaktionen und Löschgrenzen (API 1, ab 0.1.17)

`Plugin.settings` deklariert `Setting(name, default)` für nicht geheime Skalare;
`settings_permission` verweist auf ein zusätzliches Plugin-Recht.
`plugin_api.settings.read_settings/save_settings` prüfen frischen Kontostatus,
Einstieg, gespeicherte Plugin-Pause und beim Schreiben das zusätzliche Recht.
Speicherung und Audit sind atomar; keine Inhalte im Ereignis. Das Core-Testplugin
zeigt eine übersetzte Beispielpflege. Keine neue Migration.

`plugin_api.files.store_file(..., connection=connection)` kann eine aktive
NeoFab2-Transaktion verwenden; Rollback entfernt auch den Upload. Dateizugriffe
beachten jetzt die gespeicherte Pause sofort. Kein Lösch-Hook, keine automatische
Benutzer- oder Dateibereinigung. [Vollständiger Vertrag, Grenzen und Prüfung](Core_Plugin_Dienstvertraege.md).
