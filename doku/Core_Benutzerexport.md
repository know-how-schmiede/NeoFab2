# Benutzerexport – 0.1.9 (Benutzervorgabe vom 25.09.2026)

U09/U06/S09: Export aller aktuellen NeoFab2-Konten, einschließlich gesperrter und
auf Aktivierung wartender Konten. Benutzerverwaltung → **Benutzer exportieren**.
Der Download heißt `neofab2-users.json`. Nur aktive Administratoren erhalten
Zugriff; POST und CSRF schützen den Aufruf. Die aktuelle Listenseite oder ein
Seitenfilter begrenzen den Export nicht.

Die Datei enthält personenbezogene Profile und **Passwort-Hashes**. Geschützt
aufbewahren und nicht in Git, E-Mails oder öffentliche Tickets übernehmen.
Sitzungen, Aktivierungs-/Resetcodes, Dateien, Plugin-Daten und Importhistorie
sind ausgeschlossen. Der Export ersetzt keine vollständige Sicherung.

## Format und erneuter Import

JSON-Format **2** verwendet `format`, `source` und `users` wie der bestehende
[Importvertrag](Core_Benutzerimport.md). Unterschied zu Altformat 1:

- Native Rollen `user`, `staff`, `admin`; `worker` bleibt nur in Altformat 1 gültig.
- Zusätzliches boolesches Pflichtfeld `activation_pending`, damit wartende Konten
  nicht unbeabsichtigt freigeschaltet werden.
- Quell-ID ist die NeoFab2-Konto-ID. Profile, Passwort-Hash, Erstellungszeit,
  Aktivstatus, Sprache und Theme bleiben enthalten; `deleted` ist false,
  weil NeoFab2 derzeit keine gelöschten Konten speichert.

Die Anwendung erzeugt beim ersten Export eine zufällige stabile Quellkennung
unter `core.users.export_source` in der vorhandenen Einstellungstabelle. Sie bleibt
über Neustarts und Wiederholungen erhalten. Sicherung/Restore muss sie mitnehmen.
Eine Datenbankkopie behält diese Identität; zwei auseinanderentwickelte Kopien
nicht als dieselbe Quelle importieren. Beschädigte Kennungen werden nicht still
ersetzt. Eigenständige neue Installationen erhalten eigene Kennungen.

Der bestehende Import akzeptiert beide Formate. Vorschau und Bestätigung bleiben
verpflichtend; Rollen-/Kollisions-/Hash-/Auswahllistenregeln gelten weiter.
Vor allem müssen benötigte Positionen, Studiengänge und Kostenstellen im Ziel
bereits existieren. Wiederholter Import derselben Quelle erzeugt keine Duplikate.
Export und Import zurück in dieselbe Installation sind **kein Restore**:
vorhandene gleichnamige E-Mails werden weiterhin als Konflikte abgewiesen.

Bis 5000 Konten und 8 MiB. Bei Überschreitung kein Teil-Export. Im Browser bleibt
für einen späteren Import das bestehende Request-Limit von 1 MiB einschließlich
Multipart-Overhead bestehen; größere zulässige Dateien über CLI importieren.
Ein Export aus einer leeren Installation ist über den lokalen Betriebszugang
möglich und enthält eine leere Benutzerliste.

## Lokaler Export

Als **root**, ausgeführt durch **neofab2**, Standardinstallation:

```bash
install -d -m 0700 -o neofab2 -g neofab2 /var/lib/neofab2/export
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml \
  /opt/neofab2/.venv/bin/neofab2 users-export \
  --output /var/lib/neofab2/export/neofab2-users.json
stat -c '%a %U %n' /var/lib/neofab2/export/neofab2-users.json
```

Erwartet: Datei mit Modus **600**, Besitzer **neofab2**, Erfolgsmeldung ohne
Benutzerdaten oder Hashes auf der Konsole. Vorhandene Dateien werden nicht
überschrieben; für den nächsten Export einen neuen Namen wählen.
Die CLI verwendet privilegierten lokalen Betriebszugriff wie der bestehende
CLI-Import; es ist keine Webanmeldung erforderlich.

Der Audit-Eintrag `users.exported` enthält nur Akteur-ID (bei Webzugriff) und
Anzahl der Konten. Er belegt die Erstellung, nicht die dauerhafte Speicherung
beim Empfänger. Ein fehlgeschlagener Audit-Schreibvorgang verhindert die
Auslieferung. Ein späterer Verbindungs-/Dateifehler kann trotz erstelltem
Audit-Eintrag die vollständige Zustellung verhindern. Keine Hashes in Audit,
HTML-Formular, Session oder Fehlerantwort. Download mit `no-store`, Attachment
und `nosniff`; Daten werden ausschließlich in der angeforderten JSON-Datei geliefert.

## Version, Update und Fehlerhilfe

Die Version lautet ausdrücklich **0.1.9**, wie am 25.09.2026 beauftragt.
Diese Nummer wurde bereits am 19.09.2026 für einen älteren Stand verwendet.
Der neue Eintrag in der Versionshistorie unterscheidet beide Stände über Datum
und Funktionsumfang. Es findet **kein Code- oder Schema-Rückbau** statt:
Schema bleibt **`0012_user_import`**. Keine zusätzliche Migration.

Normalen [Updateablauf](SETUP.md) verwenden. Bei einer vorhandenen Installation
mit der gleichnamigen alten Paketversion gegebenenfalls den aktuellen Checkout
explizit neu installieren (Standardpfade, **root**, im kontrollierten
Update-/Wartungsfenster mit gestopptem Web-/Workerbetrieb):

```bash
runuser -u neofab2 -- /opt/neofab2/.venv/bin/python -m pip install --force-reinstall --no-deps /opt/neofab2
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version 0.1.9, Schema bereit; nach dem geregelten Neustart ist der neue
Exportknopf vorhanden. Der erste Befehl installiert nur den aktuellen lokalen
Checkout erneut; vorausgesetzt sind die bereits installierten Abhängigkeiten.
Bei einem alten Schema zunächst die bestehenden Migrationen über den normalen
Updateweg ausführen, nicht Versionsnummer und Schemastand gleichsetzen.

403: aktives Admin-Konto prüfen. 400: Formular neu öffnen oder Exportgrenzen
prüfen. 503: Schema/Datenbank/Audit prüfen. CLI-Fehler: Ausgabeverzeichnis und
Schreibrechte prüfen, neuen Dateinamen wählen. Beschädigte Exportkennung aus
einer geprüften Sicherung wiederherstellen; kein unkontrollierter Identitätswechsel.

## Prüfung

Nur synthetische Konten. Rechte/CSRF, Downloadheader, Profil-/Hash-/Status-Rundlauf,
Wiederholungen und parallele Exporte, Neustart, Limits, Audit-Rollback sowie
CLI-Dateirechte und Überschreibschutz werden in `tests/core/test_user_export.py`
geprüft. Als **Entwicklungsbenutzer**, im Repository mit Entwicklungsumgebung:

```bash
python -m pytest -q tests/core/test_user_export.py tests/core/test_user_import.py
python -m pytest -q
python -m build
```

Keine produktiven Konten exportiert/importiert; Browser-/LXC-/Core-Abnahme und
P1/P2 bleiben offen.
