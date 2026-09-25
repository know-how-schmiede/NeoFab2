# Datei- und Plugin-Dienstverträge – 0.1.17

Ergänzung 0.1.20: Die [bestätigte Löschung deaktivierter Core-Konten](Core_Benutzerloeschung.md) ist nun umgesetzt. Dateibesitz, unbekannte Tabellen/Plugins und ungeklärte Versandbezüge blockieren sie. Die nachfolgenden Aussagen zu 0.1.17 beschreiben den damaligen Stand; allgemeine Plugin-Lösch-Hooks und jährliche Bereinigung bleiben Planung.

Paket 5, Basisumfang: S10, N01, U05/N06 als Löschvertrag sowie U06/S09/X05–X07.
Nur technische Testplugins. API bleibt 1, Testplugins bleiben 0.1.0.
P1/P2 (eigene Plugin-Verzeichnisse und Mindestzugriff) sind weiterhin ausdrücklich
nur geplant. Damit ist der hier beschriebene Basisumfang umgesetzt, das um P1/P2
erweiterte Gesamtpaket 5 jedoch noch nicht abgeschlossen. Keine Core-Abnahme.

## Plugin-Einstellungen

Plugins deklarieren ein unveränderliches Tupel `settings` aus `Setting(name,
default)` und ein zusätzliches `settings_permission`. Dieses Recht muss in
`permissions` des eigenen Plugins stehen; das Einstiegsrecht genügt nicht zum
Schreiben. Ohne Deklaration ist der Dienst nicht verfügbar. Bestehende Plugins
ohne Einstellungen bleiben gültig.

```python
from neofab2.plugin_api import Permission, Setting
from neofab2.plugin_api.settings import read_settings, save_settings

# Zusätzliche Felder im Plugin(...):
# permissions=(Permission("example.configure", ("admin",)),),
# settings=(Setting("caption", "Test"), Setting("count", 3)),
# settings_permission="example.configure",

# Innerhalb eines authentifizierten Requests dieses Plugins:
# values = read_settings("example")
# save_settings("example", {"caption": "Synthetic", "count": 4})
```

Bis zu 32 Werte: Text bis 2000 Zeichen, Boolean oder vorzeichenbehaftete
64-Bit-Ganzzahl. Der Standard legt den exakten Typ fest; `True` ist keine
Ganzzahl. Namen: Kleinbuchstabe gefolgt von höchstens 31 Kleinbuchstaben,
Ziffern oder Unterstrichen. Der vollständige Speicherschlüssel darf 100 Zeichen
nicht überschreiten. Keine Listen, verschachtelten Objekte oder frei wählbaren
Core-Schlüssel. Alle deklarierten Werte müssen beim Speichern enthalten sein.
Domänenspezifische Regeln prüft zusätzlich das Plugin.

Speicherung in vorhandener Tabelle `core_settings`, Schlüssel
`plugin.<kennung>.<name>`, JSON-Skalar. Fehlende Werte liefern den Standard;
beschädigte Werte ergeben einen Fehler statt stillschweigender Ersatzwerte.
Ein berechtigtes vollständiges Speichern repariert sie. Unbekannte alte Schlüssel
werden weder gelesen noch automatisch gelöscht. Änderungen an Name oder Typ
bestehender Einstellungen benötigen einen ausdrücklichen Migrationsplan.

Lesen setzt aktuellen aktiven Kontostatus, abgeschlossene Aktivierung und
Plugin-Einstieg voraus. Schreiben verlangt zusätzlich das deklarierte Recht;
kein Admin-Wildcard. Gespeicherte Deaktivierung und pausierte Abhängigkeiten
sperren den Dienst bereits in laufenden Prozessen. Eine neue Aktivierung braucht
weiterhin den dokumentierten Neustart, wenn das Plugin noch nicht geladen war.
**Keine Geheimnisse oder personenbezogenen Daten speichern:** alle zum Einstieg
berechtigten Konten dürfen die Einstellungen lesen. SMTP-Passwörter bleiben in
der geschützten Betriebskonfiguration. Der Dienst erkennt Geheimnisse nicht am
Inhalt. Formulare benötigen wie bisher CSRF-Schutz und Jinja-Escaping.

Eine Änderung und ihr Audit-Ereignis sind atomar. Das Ereignis enthält nur
Plugin-ID, deklariertes Einstellungsrecht und Benutzer-ID, keine Werte.
`connection=` akzeptiert eine aktive Transaktion auf der NeoFab2-Engine.
Ein Savepoint verhindert teilweise Einstellungen auch dann, wenn der Aufrufer
einen Fehler abfängt. Ohne Verbindung verwaltet der Dienst seine Transaktion.
Bei parallelen vollständigen Änderungen gilt der zuletzt gespeicherte Stand;
keine automatische Zusammenführung konkurrierender Formulare.

## Dateien und gemeinsame Transaktionen

`plugin_api.files.store_file(plugin_id, upload, connection=None)` kann nun dieselbe
aktive Transaktion wie Plugin-Daten, Versand und Audit verwenden. Ein Rollback
des Aufrufers verwirft auch die Datei. Ohne Verbindung wird wie bisher sofort
in einer eigenen Transaktion gespeichert. Fremde Engines oder Verbindungen ohne
aktive Transaktion werden vor dem Schreiben abgewiesen.

Dateien bleiben in `core_files` als SQLite-BLOB mit generierter ID, Modulkennung
und aktueller Benutzer-ID. Kein frei übergebbarer Besitzer, Modulwechsel oder
Dateisystempfad. Unbekannte Module einschließlich `core` sind keine Dateiplugins.
Datei- und Einstellungsdienst prüfen gespeicherte Plugin-Pause und den frischen
Kontostatus; deaktivierte und auf Aktivierung wartende Konten sind gesperrt.
Downloadrechte bleiben getrennt für eigene und alle Dateien. Andere Module und
fremde Besitzer ohne breites Recht erhalten keine Inhalte. Namen mit Pfadzeichen,
Steuerzeichen, leerem Inhalt oder unerlaubter Endung werden abgewiesen.

Grenzen unverändert: maximal 1 MiB je deklarierter Datei; `management_test` erlaubt
nur TXT bis 256 KiB. Zusätzlich gilt das globale Request-Limit einschließlich
Multipart-Overhead. Downloads als Attachment/Octet-Stream, `nosniff` und `no-store`.
Die Endungsprüfung ist kein Virenscanner und keine Inhaltsvalidierung. Keine
Vorschau, kein Streaming großer Fertigungsdateien, keine Gesamtquote und keine
neue Dateilöschfunktion. Größere Dateien und fachliche Vorschauen folgen mit dem
beauftragten Fachumfang. [Bestehende Rechte und Limits](Core_Dateien_und_Rechte.md).

## Zuständigkeiten der übrigen Dienste

| Dienst | Öffentlicher Vertrag | Verantwortung des Plugins |
|---|---|---|
| Versand | `plugin_api.notifications.enqueue_email`, persistente Outbox, optional `connection` | Empfänger-/Objektrecht, Inhalt und stabiler Idempotenzschlüssel; kein direkter SMTP-Versand |
| Audit | `plugin_api.audit.record_action`, optional `connection` | Deklarierte Aktion, vorherige Objektprüfung; keine Geheimnisse im Ereignis |
| Aufgaben | Deklarierte `Plugin.tasks`, vorhandenes CLI | Vertrauenswürdiger Code, begrenzte und wiederholbare Arbeit; kein impliziter Benutzerkontext |
| Übersetzungen | `Plugin.translations`, `plugin_api.i18n` | Englischer Ausgangstext, DE/FR-Katalog, sichere Ausgabe |
| Einstellungen/Dateien | Obige Request-Dienste | Eigene Fachvalidierung, CSRF und Besitzer-/Objektregeln |

Die Request-Dienste dürfen nicht durch künstliches Setzen von `g.current_user`
in Hintergrundaufgaben als privilegierte Systemdienste verwendet werden. Ein
allgemeiner Hintergrundzugriff mit Service-Identität ist nicht Teil dieses
Vertrags. Aufgaben/Versand behalten ihre bereits dokumentierten Ausführungsgrenzen.
Plugins sind vertrauenswürdiger Python-Code; diese Schnittstelle ist keine Sandbox.

## U05/N06: verbindliche Grenze vor einer Löschimplementierung

In 0.1.17 gibt es weiterhin **keine Benutzerlöschung und keine jährliche
Plugin-Bereinigung**. Konten werden deaktiviert; Besitzer-IDs, Dateien,
Einstellungen und Audit-Zuordnungen bleiben erhalten. Deaktivierung eines Plugins
löscht ebenfalls nichts. Eine Wiederaktivierung kann vorhandene Daten wieder
zugänglich machen. Bestehende Audit-Aufbewahrung ist davon unabhängig.

Für eine spätere Löschimplementierung gelten folgende Voraussetzungen:

1. Getrennte Aktionen für Kontosperre, Anonymisierung, endgültige Benutzerlöschung,
   fachliche Bereinigung und Plugin-Deinstallation; keine implizite Kaskade.
2. Schreibfreie Vorschau mit Benutzer-/Modul-/Objekt-IDs, UTC-Stichtag, betroffenen
   Dateien, Anzahl, Ausschlussgründen und Versionsstand der Auswahl. Nie allein
   aufgrund des Alters Benutzer oder Stammdaten auswählen.
3. Jedes installierte betroffene Plugin muss seine Benutzerbezüge und
   Aufbewahrungsregeln beschreiben, auch wenn es deaktiviert ist. Bei fehlender
   oder unbekannter Auskunft bleibt der Benutzer erhalten. Kein Import fremden
   oder fehlenden Codes allein für eine Löschprüfung.
4. Explizite berechtigte Bestätigung einer unveränderten Vorschau; aktuelle
   Rechte und Referenzen unmittelbar vor Ausführung erneut prüfen. Bei geänderten
   Daten neue Vorschau verlangen. Letzten aktiven Admin niemals entfernen.
5. Abgeschlossene Fachvorgänge getrennt nach Modul behandeln; Dateien nur nach
   Prüfung ihrer Referenzen gemeinsam mit den zugehörigen Datensätzen entfernen.
   Versandaufträge, Qualifikationen und externe Referenzen ausdrücklich bewerten.
6. Atomare lokale Arbeitsschritte, persistenter Fortschritt, idempotente
   Wiederaufnahme nach Fehlern, Audit ohne personenbezogene Nutzlast und
   Ergebnisbericht. Sicherungen haben eine eigene Aufbewahrungsregel; Restore
   kann entfernte Daten wiederherstellen und braucht einen dokumentierten Ablauf.

Dies definiert den Vertrag, implementiert aber keine ausführbaren Lösch-Hooks,
Fristen oder produktiven Bereinigungsjobs. Das erste Fachplugin konkretisiert
Objekt-/Aufbewahrungsregeln vor Umsetzung; produktive Löschungen brauchen einen
gesonderten Auftrag. Der spätere Import darf gelöschte Altbenutzer nicht ohne
vorherige Entscheidung wieder aktivieren (Paket 6).

## Bedienung und Prüfung

Normalen Updateweg aus [SETUP](SETUP.md) verwenden. Keine neue Migration;
Schema bleibt `0011_audit_status`. Bestehende Dateien/Einstellungen bleiben erhalten.
Als **root**, ausgeführt durch **neofab2**, mit Standardpfaden:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version **0.1.17**, Schema bereit. In einer isolierten Testinstallation
als Admin unter Plugin-Verwaltung `core_test` aktivieren und Webprozesse neu
starten. Seine Seite zeigt „Testeinstellung“ (englischer Standardwert
`Synthetic test`). Nur synthetischen Text speichern, Seite neu laden und
Persistenz nach Neustart prüfen. `management_test` benötigt zusätzlich
`core_test`; eine kleine synthetische TXT-Datei zum Dateitest verwenden.
Die Testplugins bleiben standardmäßig aus.

Fehlerhilfe: 403 → aktives Konto und deklarierte Plugin-Rechte prüfen; 404 beim
Dateidienst → aktive Auswahl einschließlich Abhängigkeiten prüfen; 400 → CSRF,
Eingaben und Grenzen prüfen; 413 → kleinere Testdatei verwenden. Nach dem
Deaktivieren kann die Dateitestseite sofort 404 und die Einstellungstestseite
403 liefern, obwohl die Route bis zum Neustart noch registriert ist. Navigation
und geladener Plugin-Stand werden weiterhin erst mit Neustart abgeglichen.
Bei beschädigten Einstellungen vollständig gültige Werte über den autorisierten
Dienst speichern oder eine geprüfte Sicherung wiederherstellen; keine Schema-
oder Datenkorrektur beim normalen Seitenaufruf.

Als **Entwicklungsbenutzer**, im Repository, vorhandene Entwicklungsumgebung:

```bash
python -m pytest -q
python -m build
```

Automatisierte Nachweise: `tests/plugin_contract/test_plugin_settings.py`,
`test_files.py`, `test_management.py` sowie vorhandene Versand-/Audit-Tests.
Synthetische HTTP-/CSRF-/Rechteprüfungen, Typen/Grenzen, fremde Transaktion,
Auditfehler/Rollback, gemeinsame Speicherung, Namensraum, zweiter App-Prozessstand,
Neustart und SQLite-Sicherung/Restore. Interaktive Browser- und echte
Debian-/LXC-Abnahme bleiben offen.
