# NeoFab2 – Versionshistorie

## Version 0.1.9 – 2026-09-25 (erneute Versionsvergabe auf Benutzerwunsch)

Bereich: fehlenden NeoFab2-Benutzerexport ergänzen (U09/U06, U05/U07/N04,
S09/S12/X05–X07). Der Benutzer hat ausdrücklich **0.1.9** angegeben.
Die frühere gleichnamige Version vom 19.09.2026 bleibt unten dokumentiert.
Kein Code-/Schema-Rückbau gegenüber 0.1.18; API 1/Testplugins 0.1.0 unverändert.

### Änderungen

- „Benutzer exportieren“ in der Benutzerverwaltung: Admin-/POST-/CSRF-geschützter
  JSON-Download aller Konten, einschließlich deaktivierter und wartender Konten.
- `users-export --output ...` schreibt neue Dateien mit 0600 ohne Überschreiben;
  keine Benutzerdaten oder Hashes auf der Konsole.
- Natives Format 2 mit stabiler automatisch gespeicherter Quellkennung, Konto-IDs,
  Profil, Passwort-Hashes, nativen Rollen, Sprache/Theme und Aktivierungsstatus.
  Keine Sitzungen, Kontocodes, Fachdateien oder Plugin-Daten im Export.
- Bestehender Import akzeptiert Format 2 zusätzlich zum unveränderten Altformat 1.
  Wartende Konten bleiben wartend, Mitarbeiter behalten die Rolle staff.
  Wiederholung/Quellzuordnung und bestehende Kollisionsregeln bleiben wirksam.
- Audit protokolliert Erstellung mit Akteur und Anzahl, ohne personenbezogene
  Nutzlast. Download als Attachment, mit no-store und nosniff.
- Deutsche Anleitung und EN/DE/FR-Beschriftungen ergänzt.

### Betrieb und Migration

**Keine neue Migration**, Schema bleibt `0012_user_import`.
Die erste Exporterstellung speichert `core.users.export_source` in der bestehenden
Einstellungstabelle. Diese Kennung mit Konten sichern und wiederherstellen.
Exportgrenzen: 5000 Konten/8 MiB; für erneuten Webimport gilt weiterhin das
1-MiB-Requestlimit, größere zulässige Dateien über CLI importieren.

Normalen Updateablauf verwenden. Wegen der erneut vergebenen Versionsnummer bei
Bedarf aktuellen Checkout explizit neu installieren; kopierbare Befehle und
Fehlerhilfe stehen in [Benutzerexport](Core_Benutzerexport.md). Ein alter
0.1.9-Paketstand ist nicht dieser neue Stand. Kein Downgrade der Datenbank.
Als **root**, Ausführung durch **neofab2**, Standardpfade:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: **0.1.9**, Schema bereit, Exportknopf in der Benutzerverwaltung.
Exportdateien enthalten Passwort-Hashes und persönliche Daten: geschützt halten.
Der Benutzerexport ersetzt keine vollständige Sicherung und führt im Quellsystem
keine Löschungen aus. Kein produktiver Export oder Import durch Codex.

### Prüfungen

- **379 Gesamttests bestanden**, Python 3.13; darunter 14 neue Exporttests.
- Export-/Importtests zusammen: 73 bestanden; native Rollen, Profil/Hashes,
  gesperrte/wartende Konten, strikte Typen und wiederholbarer Rundlauf geprüft.
- Admin-/Direktzugriff, CSRF, frischer Kontostatus, Downloadheader, private Datei,
  Überschreibschutz, Limits, Auditfehler und Geheimnisschutz geprüft.
- Stabile Quellkennung bei Parallelität und Neustart geprüft.
- Wheel/Quelldistribution 0.1.9 gebaut; separat installiertes Wheel einschließlich
  Benutzerexport erfolgreich geprüft. CLI-Version, Dokumentationslinks und Diff geprüft.

Grenzen: synthetische Daten, keine interaktive Browser-/LXC-/Core-Abnahme.
P1/P2 bleiben offen. Kein Commit oder Push.

### Commit für GitHub Desktop

Commit-Titel:

```text
feat: NeoFab2 0.1.9 – Benutzerexport über Oberfläche und CLI ergänzen
```

Commit-Beschreibung:

```text
Fehlenden NeoFab2-Benutzerexport mit Admin-/CSRF-Schutz und privater CLI-Datei ergänzen.
Natives Format 2 mit stabiler Quellkennung, Profilen, Rollen und Aktivierungsstatus liefern.
Erneuten Import inklusive wartender Konten und Mitarbeiterrolle staff unterstützen.
Sitzungen und Tokens ausschließen; Exporterstellung ohne Nutzdaten auditieren.
379 Tests, Export-/Importrundlauf, Paketbau und installiertes Wheel prüfen.
Version auf ausdrücklichen Benutzerwunsch erneut 0.1.9 setzen und Historie abgrenzen.
Keine neue Migration; Schema bleibt 0012_user_import, keine Produktivübernahme.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.18 – 2026-09-25

Bereich: Core-Paket 6 (U09/N04/U06, U01/U04/U05/U07/U08, S09/S12, X05–X07).
Version auf Benutzerauftrag; Plugin-API bleibt 1, technische Testplugins 0.1.0.

### Änderungen

- Geschützter Benutzerexport aus einer eigenständigen NeoFab-SQLite-Kopie mit
  stabilen Alt-IDs, Installationskennung, Rollen/Status, Profil, Sprache und Theme.
  Quelle ausschließlich lesend; keine NeoFab-Codeimporte oder Tokenübernahme.
- Benutzerimport mit Admin-Oberfläche und lokalem CLI: schreibfreie Vorschau,
  Ergebnisbericht, explizite Bestätigung und atomare Speicherung mit Audit.
  HMAC-gebundener Plan verhindert Import nach unbemerkten Quell-/Zieländerungen.
- Feste Regeln: `worker` → `staff`, unbekannte Rollen und E-Mail-Kollisionen
  blockieren; gelöschte neue Altbenutzer überspringen. Keine Kontozusammenführung
  anhand der E-Mail. Inaktive Konten bleiben inaktiv.
- Begrenzte Werkzeug-scrypt-/PBKDF2-Kompatibilität; unbrauchbare Hashes ergeben
  gesperrte Konten mit ausstehender Aktivierung und unbekanntem Zufallspasswort.
  Passwort/Freischaltung anschließend administrativ entscheiden; kein Versand.
- Wiederholungen erzeugen keine Duplikate. Geänderte Quelle aktualisiert nur
  unveränderte zugeordnete Zielkonten; lokale Änderungen bleiben geschützt.
  Aktualisierte Konten verlieren Sitzungen und offene Kontocodes.
- Deutsche Betriebsanleitung, EN/DE/FR-Oberfläche, Funktionsmatrix und Core-Plan
  ergänzt. Paket 7 ist der nächste unabhängige Schritt; P1/P2 bleiben offen.

### Betrieb und Migration

**Neue explizite Migration `0012_user_import`**: `core_user_imports` speichert
Quellkennung/Alt-ID, eindeutige Ziel-ID und Fingerabdrücke. Bestehende Konten
bleiben erhalten, Schemaänderungen erfolgen nicht beim Webstart.
Normalen Updateweg mit Sicherung, Migration und Neustart verwenden.
Als **root**, ausgeführt durch **neofab2**, Standardpfade:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: **0.1.18**, Datenbank/Schema bereit. Der bisherige NeoFab-Webexport
enthält keine stabilen IDs/Theme und ist kein direktes Importformat.
[Vorbereitung, Vorschau, Bestätigung, Fehlerhilfe und Rückfall](Core_Benutzerimport.md).
Exporte enthalten Passwort-Hashes; Werkzeug schreibt neue Dateien mit 0600.
Berichte enthalten keine Hashes, können aber personenbezogene E-Mails enthalten.

Backup und Restore müssen Konten und Importzuordnungen gemeinsam enthalten.
Für einen Rückfall vor Migration passende vollständige Sicherung und Codeversion
verwenden. Kein Produktivimport oder Produktivschema durch Codex ausgeführt.

### Prüfungen

- **365 Gesamttests bestanden**, Python 3.13; davon **59 neue Importtests**.
- Rollen, Aktivstatus, gelöschte Konten, Profiloptionen, E-Mail-Kollisionen,
  unbekannte Felder/Rollen, Format-/Größenlimits und Hash-Arbeitsgrenzen geprüft.
- Echte Anmeldung mit synthetischen scrypt- und PBKDF2-Hashes; Sperre bei ungültigem
  Hash, Letzter-Admin-Schutz sowie Sitzungs-/Kontocodewiderruf geprüft.
- Schreibfreie Vorschau, Wiederholung/Neustart, lokale Zieländerungen, veraltete
  oder ungültige Plan-Werte, parallele Bestätigung und vollständiger Rollback
  bei Audit-/Datenbankfehler geprüft.
- Admin-/Direktzugriff, CSRF, CLI-Abbruch/Bestätigung, geschützter Export ohne
  Überschreiben und Geheimnisschutz in HTML/Session/CLI/Fehlerprotokoll geprüft.
- Upgrade von 0011, Wiederholung und Datenerhalt, Readiness, Start ohne
  Schemaanlage und SQLite-Sicherung/Restore einschließlich Importzuordnung geprüft.
- Wheel und Quelldistribution gebaut; separat installiertes Wheel aus neutralem
  Verzeichnis einschließlich Importvorschau, Ausführung und Wiederholung geprüft.
- CLI meldet 0.1.18; relative Dokumentationslinks und `git diff --check` bestanden.

Grenzen: ausschließlich synthetische Daten, keine produktive Benutzerübernahme,
kein realer Altpasswortnachweis, keine interaktive Browser-/Debian-/LXC-Abnahme.
Allgemeiner NeoFab2-Kontoexport und Konfliktzusammenführung nicht implementiert.
P1/P2 und vollständige Core-Abnahme bleiben offen. Kein Commit oder Push.

### Commit für GitHub Desktop

Commit-Titel:

```text
feat: NeoFab2 0.1.18 – Benutzerimport mit Vorschau und Ergebnisbericht
```

Commit-Beschreibung:

```text
Core-Paket 6 mit lesendem Export aus einer NeoFab-SQLite-Kopie implementieren.
Admin-/CLI-Vorschau und bestätigten atomaren Benutzerimport mit Audit ergänzen.
Stabile Quellzuordnung, Wiederholung und Schutz lokaler Zieländerungen umsetzen.
Rollen-, Status-, Kollisions- und begrenzte Hash-Kompatibilitätsregeln definieren.
Keine alten Tokens übernehmen; Sitzungen und Kontocodes bei Updates widerrufen.
Explizite Migration 0012_user_import und Readiness ergänzen.
365 Tests einschließlich 59 Importtests, Paketierung und installiertes Wheel prüfen.
Deutsche Anleitung, Funktionsmatrix, Core-Plan und Versionshistorie aktualisieren.
Kein Produktivimport; P1/P2 und vollständige Core-Abnahme bleiben offen.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.17 – 2026-09-25

Bereich: Basisumfang Core-Paket 5 (S10/N01, U06/S09, U05/N06 als
Dokumentationsvertrag, S12/X05–X07). Version auf Benutzerauftrag;
Plugin-API bleibt 1 und technische Testplugins bleiben 0.1.0.

### Änderungen

- Deklarierte nicht geheime Plugin-Einstellungen mit strikten Namen, Typen und
  Grenzen, eigenen Namensräumen und explizitem Schreibrecht. Aktueller Kontostatus,
  Einstieg und gespeicherte Plugin-Pause werden serverseitig geprüft.
- Speicherung und Audit ohne Werte atomar; optional gemeinsame Transaktion mit
  dem Aufrufer. Savepoint und explizite SQLite-Transaktion verhindern Teilstände
  bei Auditfehlern sowie vorzeitigen Commit bei `engine.begin()`.
- Core-Testplugin um persistente Testeinstellung mit DE/FR-Beschriftung ergänzt.
- Dateiuploads können eine gemeinsame Transaktion verwenden. Dateioperationen
  beachten gespeicherte Deaktivierung und Aktivierungsstatus sofort; Dateidaten
  bleiben erhalten. Bestehende Pfad-, Besitzer- und Größenregeln gelten weiter.
- Benutzerlöschung und jährliche Bereinigung abgegrenzt: Vorschau, Referenzen,
  Bestätigung, Aufbewahrung, Wiederaufnahme und Restore als Vertrag dokumentiert.
  Keine Löschfunktion oder Fachplugins umgesetzt.
- Deutsche Anleitung, Plugin-Vertrag, Funktionsmatrix und Core-Plan aktualisiert.
  Der Basisumfang von Paket 5 ist umgesetzt; P1/P2 bleiben ausdrücklich nur
  geplant und damit das erweiterte Gesamtpaket 5 offen. Paket 6 ist der nächste
  unabhängige Core-Ausbau. Keine vollständige Core-Abnahme.

### Betrieb und Migration

Keine neue Migration; Schema bleibt `0011_audit_status`. Plugin-Einstellungen
verwenden die vorhandene Tabelle `core_settings` unter `plugin.<kennung>.*`.
Normalen Updateablauf verwenden. Alle Webprozesse anschließend neu starten,
damit Registrierung und Navigation zur gespeicherten Auswahl passen.
Datei-/Einstellungsdienste sperren deaktivierte Plugins schon vor dem Neustart.
Als **root**, ausgeführt durch **neofab2**, Standardpfade:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: **0.1.17**, Schema bereit. Testplugins bleiben standardmäßig aus.
Bedienung, Standards und Fehlerhilfe: [Datei- und Plugin-Dienstverträge](Core_Plugin_Dienstvertraege.md).
Vorhandene Dateien werden nicht gelöscht. Keine Produktivmigration ausgeführt.

### Prüfungen

- **306 Gesamttests bestanden**, Python 3.13; davon 24 neue Vertragstests.
- HTTP/CSRF/Rollen, Escaping, Typen/Grenzen, Namensraumtrennung, fehlende Rechte,
  deaktivierte/wartende Konten, beschädigte Werte, sofortige Pause über zwei
  App-Instanzen und Datenerhalt bei Wiederaktivierung geprüft.
- Gemeinsamer Commit und Rollback mit Datei/Einstellung/Audit, fremde Engine,
  fehlende Transaktion, abgefangener Auditfehler und SQLite-Savepoint geprüft.
- Neustart und synthetische SQLite-Sicherung/Wiederherstellung geprüft.
- Wheel/Quelldistribution 0.1.17 gebaut; separat installiertes Wheel aus neutralem
  Verzeichnis einschließlich Speichern der Testeinstellung erfolgreich geprüft.
- CLI-Version, relative Dokumentationslinks und `git diff --check` bestanden.

Grenzen: keine interaktive visuelle Browserabnahme oder echte Debian-/LXC-Abnahme.
Keine P1–P5-Umsetzung, keine Produktivdaten, kein Zugriff auf das alte NeoFab.
Benutzerlöschung/Bereinigung nur definiert. Kein Commit oder Push.

### Commit für GitHub Desktop

Commit-Titel:

```text
feat: NeoFab2 0.1.17 – Datei- und Plugin-Dienstverträge
```

Commit-Beschreibung:

```text
Core-Paket 5 im Basisumfang um deklarierte Plugin-Einstellungen ergänzen.
Namensräume, Typen, Schreibrechte, frischen Kontostatus und Plugin-Pause prüfen.
Einstellungen samt Audit und Dateiuploads in gemeinsamen Transaktionen unterstützen.
SQLite-Savepoint-Rollback auch bei engine.begin() absichern.
Testeinstellung im Core-Testplugin und Lösch-/Bereinigungsvertrag dokumentieren.
306 Tests, Paketbau, installiertes Wheel, CLI-Version und Dokumentationslinks prüfen.
Keine neue Migration; P1/P2 und vollständige Core-Abnahme bleiben offen.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.16 – 2026-09-23

Bereich: Core-Paket 4 (S01–S04/S08, U06/U07, N01, S09/S12, X05–X07).
Version auf Benutzerauftrag; technische Testplugins bleiben 0.1.0.

### Änderungen

- Öffentliche Infoseite, Impressum und Datenschutz mit Administratorpflege und
  sicherer kleiner Markdown-Teilmenge. Leere Texte zeigen einen Hinweis.
- Konfigurierbare IANA-Zeitzone, UTC als Standard. Startseite, Info, Audit, Versand
  und Workerzeiten zeigen Zone und UTC-Abstand einschließlich Sommerzeit.
- Versionierter JSON-Import/-Export nur für Darstellung, öffentliche Inhalte und
  Zone; keine Geheimnisse, Konten, SMTP- oder Plugin-Freischaltungen. Strikte
  Validierung und atomare Speicherung einschließlich Audit.
- Rollenübersicht mit Core-/Plugin-Rechten; vorhandene Rollenzuordnung,
  Sitzungswiderruf und Letzter-Admin-Schutz nachgewiesen. Keine frei editierbaren
  Rechtebündel; Mindestzugriff P2 bleibt Planung.
- Deutsche/französische Texte ergänzt und isolierter Plugin-Übersetzungsvertrag
  mit englischem Fallback und geprüften Platzhaltern. Nachweis mit `core_test`.
- Betriebsanleitung, Funktionsmatrix, Core-Plan und Paketprüfung ergänzt.
  Paket 5 folgt; keine vollständige Core-Abnahme oder Fachplugin-Freigabe.

### Betrieb und Migration

Keine neue Migration; Schema bleibt `0011_audit_status`. Neue Einstellungen
verwenden `core_settings` unter `core.site.*`. Vorhandene Installationen starten
mit UTC und leeren öffentlichen Inhalten. Normalen Updateablauf verwenden.
Als **root**, ausgeführt durch **neofab2**, Standardpfade:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: 0.1.16, Schema bereit. Öffentliche Seiten als Gast und neue Einstellungen
als Admin prüfen. Vor einem Einstellungsimport bisherigen Export sichern; Fehler
und Rückfall sind in [Core-Oberfläche und Einstellungen](Core_Oberflaeche_und_Einstellungen.md)
beschrieben. Kein automatischer Versand, keine produktive Migration oder Löschung.

### Prüfungen

- **282 Gesamttests bestanden** unter Python 3.13, davon 27 neue Paket-4-Prüfungen.
- Öffentliche Seiten und Escaping, Admin-/Direktzugriff, CSRF, frischer Kontostatus,
  Import-Rundlauf, ungültige/übergroße Dateien, Geheimnisschutz und Audit-Rollback geprüft.
- Beide Sommerzeitwechsel einschließlich doppelter Herbststunde, UTC-Fallback,
  Neustart, Rollen-/Sitzungsschutz und isolierte DE/FR-Plugin-Kataloge geprüft.
- Wheel und Quelldistribution 0.1.16 gebaut; separat installiertes Wheel aus
  neutralem Verzeichnis einschließlich neuer öffentlicher und Admin-Seiten geprüft.
- CLI meldet 0.1.16; 162 relative Dokumentationslinks und `git diff --check` bestanden.

Grenzen: keine interaktive visuelle Browserabnahme und kein echter Debian-/LXC-Lauf.
Ältere Detailtexte teilweise englischer Fallback; keine vollständige Core-Abnahme.
Altes NeoFab und produktive Daten unverändert. Kein Commit oder Push.

### Commit für GitHub Desktop

Commit-Titel:

```text
feat: NeoFab2 0.1.16 – Core-Oberfläche und Einstellungen
```

Commit-Beschreibung:

```text
Core-Paket 4 mit Infoseite, Impressum, Datenschutz und sicherem Markdown ergänzen.
IANA-Zeitzone und Sommerzeitdarstellung mit eindeutigem UTC-Abstand bereitstellen.
Öffentliche Einstellungen validiert und atomar ohne Geheimnisse importieren/exportieren.
Rollenübersicht und isolierte DE/FR-Plugin-Kataloge mit englischem Fallback ergänzen.
Rollenpflege, Rechte, CSRF, Importfehler, Rollback, Sommerzeit und Paketierung prüfen.
Deutsche Betriebsanleitungen, Funktionsnachweise und nächsten Core-Schritt aktualisieren.
Keine neue Migration; vollständige Core- und Browser-/LXC-Abnahme bleiben offen.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.15 – 2026-09-21

Bereich: Core-Paket 3, Audit-Protokoll und Betriebsstatus (S09/S12/N01,
U06, X05–X07). Version auf Benutzerauftrag, technische Testplugins bleiben 0.1.0.

### Änderungen

- Zwei neue geschützte Admin-Seiten: Audit-Protokoll mit Ereignisfilter und
  Paginierung sowie Betriebsstatus mit Core-/Schema-/Plugin-Versionen,
  Plugin-Zielzustand, SMTP-Status und Versandauftragszahlen.
- Transaktionale Audit-Erfassung für An-/Abmeldung, begrenzte Fehlanmeldungen,
  zentrale Rechteablehnung, Benutzerverwaltung, Rollen-/Status-/Passwortänderungen,
  erfolgreiche Kontocode-Einlösung und Core-/SMTP-/Plugin-Einstellungen.
- Nur strukturierte Kennungen, Zeit und optionale Anzahl; keine Passwörter,
  Tokens, E-Mail-Adressen, IPs, Nachrichtentexte oder freie Konfigurationsdetails.
- Worker-Beobachtung für Beginn/Ende/Fehler, veralteter Stand nach fünf Minuten,
  Schutz vor Überschreiben durch verspäteten parallelen Lauf. Kein systemd-Probe
  und keine behauptete externe Zustellbestätigung.
- Lokales `audit-prune`: Vorschau standardmäßig 180 Tage, Löschung ausschließlich
  mit `--apply` und Bestätigung; Bereinigung wird selbst protokolliert.
- Additiver API-1-Vertrag `record_action` für deklarierte Plugin-Aktionen mit
  aktuellen Konto-/Aktivierungs-/Aktionsrechten und optional gemeinsamer Transaktion.
- Deutsche Betriebsanleitung, Core-Plan, Funktionsmatrix, Setup und Schnellstart
  ergänzt. Nächster Schritt ist Paket 4; Plugin-Pakete P1–P5 bleiben Planung.
- Nutzer bestätigt interne Testzustellung im Junk-Ordner. E-Mail-Punkt vorerst
  abgeschlossen; externe Relay-Zustellung bleibt ungeklärt. Keine SMTP-Umstellung.

### Betrieb und Migration

Neue explizite Migration **0011_audit_status** nach **0010_account_flows**:
Tabellen `core_audit_events` und `core_worker_status`, Zeitindex für Audit.
Bestandskonten, Einstellungen und Outbox bleiben erhalten; kein rückwirkendes Audit.
Vor Update eigene zusätzlich gestartete Worker stoppen; das Update-Skript steuert
Webdienst und NeoFab2-Versandtimer und erstellt eine Sicherung vor Migration.
Nach dem normalen Update als **root**, ausgeführt durch **neofab2**, prüfen:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version 0.1.15 und Schema bereit. Als Administrator beide neuen Seiten
unter Administration öffnen; Anmeldung erscheint im Audit, der nächste
Versandworker-Lauf im Betriebsstatus. Standardmäßig werden keine Audit-Daten
gelöscht. [Aufbewahrung, Fehlerhilfe und Grenzen](Core_Audit_und_Betriebsstatus.md).
Rückkehr zu vorherigem Code nur mit passender Datenbanksicherung. Altes NeoFab
und produktive Daten wurden nicht verändert.

### Prüfungen

- **255 Gesamttests bestanden** (Python 3.13), darunter zwölf neue Audit-/Status-
  Prüfungen mit Admin-/Direktzugriff, Geheimnisschutz, Transaktionsrollback,
  fehlender Audittabelle, Filter/Paginierung und deutschen Seiten.
- Aufbewahrungsgrenze, Vorschau und Bestätigung/Abbruch; Workerfehler, fehlende/
  veraltete Beobachtung und verspätetes Ergebnis; ungültige Konfiguration und
  Plugin-Neustartbedarf geprüft.
- Synthetischer Plugin-Vertrag: kein Admin-Wildcard, aktuelle Kontosperre,
  Aktivierung ausstehend, Plugin-Pause, Namespace, Rollback und fremde Engine geprüft.
- Upgrade 0010 → 0011, wiederholte Migration, Bestandswerterhalt, Neustart und
  SQLite-Sicherung einschließlich Audit-/Worker-Daten geprüft. Historischer
  Upgrade-Test legt Altbestände direkt im damaligen Schema an.
- Wheel/sdist 0.1.15 gebaut und separat installiertes Wheel einschließlich neuer
  Admin-Seiten geprüft; CLI-Version, Bash-Syntax und ShellCheck geprüft.
- 150 relative Dokumentationslinks und `git diff --check` bestanden.
- Echte Debian/LXC-/Browser-Abnahme, vollständiges HTTP-/Objekt-Audit,
  kryptografische Manipulationssicherung und vollständige Core-Abnahme bleiben offen.
- Kein Commit oder Push; keine produktive Migration oder Bereinigung ausgeführt.

### Commit für GitHub Desktop

Commit-Titel:

```text
feat: NeoFab2 0.1.15 – Audit-Protokoll und Betriebsstatus
```

Commit-Beschreibung:

```text
Core-Paket 3 mit geschützter Audit- und Betriebsstatus-Ansicht umsetzen.
Sicherheitsrelevante Ereignisse transaktional ohne Geheimnisdetails erfassen.
Worker-Beobachtung und minimalen autorisierten Plugin-Audit-Vertrag ergänzen.
Audit-Aufbewahrung mit lokaler Vorschau und ausdrücklicher Bereinigung bereitstellen.
Explizite Migration 0011, deutsche Anleitungen und Funktionsnachweise ergänzen.
255 Tests, Release-Pakete, installiertes Wheel und Betriebsskript-Prüfungen bestanden.
Interne SMTP-Zustellung bestätigt; externe Zustellung bleibt ungeprüft.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.14 – 2026-09-21

Bereich: SMTP-Administration und regelmäßiger Core-Versand (S05/N05, S01,
X02/X03/X05/X06, S12). Version auf Benutzerauftrag; Testplugins bleiben 0.1.0.

### Änderungen

- SMTP-Formular erhält eingegebenen Port, Host, Transport, Absender, Benutzername
  und Aktivierung bei abgewiesenen Speicherungen. Fehler verändern die gespeicherte
  Konfiguration nicht; Pausenanzeige verwendet weiterhin den gespeicherten Zustand.
- Service-Einrichtung ergänzt `neofab2-mail.service` und `neofab2-mail.timer`:
  erster Lauf nach 15 Sekunden, weitere Läufe 30 Sekunden nach Laufende,
  höchstens 20 Aufträge pro Lauf. SMTP bleibt standardmäßig deaktiviert.
- Update stoppt Timer und Versanddienst vor Sicherung/Migration, sichert ihre
  Unitdateien und startet den Timer nach erfolgreicher Web-Bereitschaft wieder.
  Bei Fehlern nach begonnenem Update bleiben Webdienst und Versand angehalten.
- Deutsche Betriebsanleitungen, Formularhilfe und Funktionsnachweise aktualisiert.

### Betrieb und Migration

Keine neue Migration; Schema bleibt `0010_account_flows`. Beim ersten Update
von 0.1.13 oder älter anschließend als **root im NeoFab2-Container**:

```bash
bash /opt/neofab2/script/setupNeoFabService
systemctl status neofab2-mail.timer --no-pager
journalctl -u neofab2-mail.service -n 40 --no-pager
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
```

Erwartet: Version 0.1.14, Timer aktiv; nach einem Lauf Versandzähler im Journal.
Das alte Update-Skript lädt seine Funktionen vor dem Git-Update und kann den
neuen Timer deshalb noch nicht selbst einrichten. Relay ohne Anmeldung:
Port 25, unverschlüsselter Transport, leerer Benutzername, freigegebener Host
und Absender. SMTP aktivieren und speichern, Testauftrag einplanen, Status nach
Timerlauf neu laden. [Details und Fehlerhilfe](Core_SMTP_und_Versand.md).
Ein aktiver Timer verarbeitet auch zuvor gespeicherte fällige Aufträge.
Vor Restore Timer und Versanddienst stoppen; erst nach Zustellabgleich starten.
Altes NeoFab und produktive Daten unverändert.

### Prüfungen

- 242 Gesamttests bestanden; danach 10 gezielte Betriebsprüfungen einschließlich
  zusätzlich ergänztem Fehler bei der Timer-Einrichtung bestanden.
- Port-25-Persistenz bei wiederholtem Speichern, Aktivierung und App-Neustart;
  Formulareingaben nach fehlgeschlagener Aktivierung erhalten.
- Reale SMTP-Kommunikation mit synthetischem Loopback-Relay ohne TLS/Anmeldung:
  persistenter Web-Testauftrag erfolgreich angenommen, kein zweiter Versand.
- systemd-Aktionen simuliert; Unit-Erzeugung, Erhalt vorhandener Units und
  Update-Reihenfolge/Fehler geprüft. Bash-Syntax und ShellCheck aller fünf Skripte bestanden.
- Wheel und sdist 0.1.14 gebaut. Separat installiertes Wheel geprüft.
- 84 relative Dokumentationslinks und `git diff --check` bestanden.
- Reales Zielrelay, Postfacheingang, interaktiver Browser und Debian/LXC/systemd
  nicht geprüft. Erfolgreiches Speichern setzte Port 25 im Test nicht zurück;
  reproduziert wurde das Verwerfen der Eingaben bei Validierungsfehlern.
- Keine vollständige Core-Abnahme, kein Commit oder Push.

### Commit für GitHub Desktop

Commit-Titel:

```text
fix: NeoFab2 0.1.14 – SMTP-Eingaben erhalten und Versandtimer einrichten
```

Commit-Beschreibung:

```text
SMTP-Formularwerte bei Validierungsfehlern erhalten und Port-25-Persistenz prüfen.
Regelmäßigen Versand über eigene systemd-Units in Service-Setup integrieren.
Versand beim Update vor Sicherung/Migration stoppen und danach wieder starten.
Lokalen SMTP-Dialog, Betriebssteuerung und Fehlerpfade mit synthetischen Daten prüfen.
Version, Betriebsanleitungen und Funktionsnachweise aktualisieren; Schema unverändert.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.13 – 2026-09-19

Bereich: Core-Paket 2, Registrierung, E-Mail-Aktivierung und Passwort-Reset
(U02–U04, S06, ergänzend U01/U05/U06/U08, S12 und X05–X07).
Version **0.1.13** wurde ausdrücklich beauftragt und folgt auf den vorliegenden
Stand 0.1.12. Alle drei technischen Testplugins bleiben bei **0.1.0**, API 1.

Die Versionsnummer wurde nach Benutzerkorrektur berichtigt. Funktionsumfang
und Schema-Revision bleiben unverändert; Version, Dokumentation und Commit-Text
sind auf 0.1.13 abgestimmt. Die Pakete wurden mit dieser Nummer erneut gebaut.

### Änderungen

- Neue Admin-Seite **Registrierung und Kontowiederherstellung** mit getrennten
  Freigaben für Registrierung und E-Mail-Reset. Beide starten ausgeschaltet.
  Registrierung mit bis zu 100 genauen Domains oder ausdrücklicher Freigabe aller Domains.
- Neue Registrierungskonten sind inaktiv, warten auf E-Mail-Aktivierung und
  erhalten ausschließlich die Benutzerrolle. Passwortwahl erst beim Einlösen
  des Aktivierungscodes durch den Postfachinhaber; keine Überschreibung bestehender Konten.
- Aktivierungscodes gelten 24 Stunden, Rücksetzcodes 30 Minuten ab Anforderung.
  Einmalige Verwendung, Widerruf nach Sicherheits-/Freigabeänderungen und
  serialisierte Einlösung. Passwort-Reset beendet alle bestehenden Sitzungen.
- Neuer Aktivierungscode anforderbar; gemeinsame Anfragebegrenzung je Adresse/IP
  und 60-Sekunden-Abstand. Generische Antworten verraten keinen Kontostatus.
- Aktivierungs-, Reset-, Willkommens- und Änderungsnachrichten in EN/DE/FR über
  die bestehende Outbox. Kontoänderung und Auftrag werden atomar gespeichert.
  Worker prüft aktuelle Gültigkeit; vollständige Codes stehen nicht in der
  persistenten Outbox und werden erst für die SMTP-Übertragung erzeugt.
- Codes werden in ein POST-Formular eingefügt, nicht in URLs transportiert oder
  durch GET verbraucht. Konfigurierte `PUBLIC_BASE_URL` schützt E-Mail-Links vor
  Host-Header-Manipulation. Alle neuen Buttons verwenden gemeinsame Icons.
- Benutzerliste zeigt ausstehende Aktivierung. Administratives Speichern eines
  solchen Kontos beendet das Verfahren; zum Aktivieren ist ein Anfangspasswort nötig.
- [Deutsche Betriebsanleitung](Core_Registrierung_und_Reset.md), Setup/Schnellstart,
  Funktionsmatrix und Arbeitsplan aktualisiert. Paket 3 mit Audit/Betriebsstatus
  ist der nächste offene Schritt. Plugin-Pakete P1–P5 bleiben reine Planung.
- Vorherige Repository-Prüfung und erweiterte Ignore-Regeln für Konfigurationen,
  Datenbankkopien und Schlüssel bleiben erhalten; keine sensiblen Dateien gelöscht.

### Betrieb und Migration

Explizite Revision **`0010_account_flows`** nach `0009_mail_outbox`:
`core_users.activation_pending`, `core_account_tokens`, `core_account_limits`
und zwei optionale Kontozuordnungen in der Outbox. Bestandskonten behalten
ihren Aktivstatus; das neue Merkmal ist für sie false. Keine Migration beim Start.

Vor Update alle zusätzlich gestarteten Worker/Aufrufpläne stoppen und eine
passende Datenbank-/Konfigurations-/Codesicherung erhalten. Das vorhandene
Update-Skript installiert und migriert den manuell bereitgestellten Stand.
Danach als **root**, ausgeführt durch **neofab2**, prüfen:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: Version 0.1.13 und Schema bereit. Vor bewusster Freischaltung die
tatsächliche HTTPS-Origin als `PUBLIC_BASE_URL` konfigurieren, SMTP testen,
Prozesse neu starten und Registrierungsdomains administrativ festlegen.
Der bisherige einmalige `mail-worker --limit 20` bleibt für die Zustellung nötig.
Kein automatischer Scheduler und kein automatisch versandtes produktives Mailing.

Nach Restore Kontoverfahren und Versand zuerst sperren: ältere Sicherungen
können bereits verbrauchte Codes/Sitzungen wiederherstellen. Vor Wiederfreigabe
offene Codes widerrufen und gegebenenfalls den Anwendungsschlüssel wechseln.
Anleitung enthält Standardwerte, Befehle, Ergebnisprüfung und Fehlerhilfe.
Altes NeoFab und produktive Daten wurden nicht verändert.

### Prüfungen

- Gesamtsuite: **235 Tests bestanden**. Danach ergänzte Normalisierung
  internationalisierter Domains: **42 gezielte Kontoverfahren-Tests bestanden**,
  einschließlich dieser zusätzlichen Regression.
- Geprüft: Rechte/CSRF, Domain-Grenzen, Rollenmanipulation, Kontostatus,
  Codeablauf/Einmaligkeit/Zweckbindung, Passwort- und Sitzungswiderruf,
  Anfragelimits, Parallelität, Rollback, SMTP-Pause, erneute Anforderung,
  Host-Header-Unabhängigkeit und fehlende Klartextcodes in der Datenbank.
- Upgrade vom vorherigen Schema, wiederholte Migration, Bestandswerterhalt,
  Neustart sowie SQLite-Sicherung/Wiederherstellung mit wartendem Code bestanden.
- Wheel und sdist 0.1.13 gebaut; separat installiertes Wheel mit neuen Admin-/
  Aktivierungs-/Reset-Templates, standardmäßig gesperrter Registrierung und
  bestehendem Core-/Plugin-Umfang erfolgreich geprüft.
- Relative Dokumentationslinks und `git diff --check` geprüft.
- Kein echter SMTP-/Postfach-Test, keine visuelle Browserabnahme und kein eigener
  Debian/LXC/systemd-Lauf. Weitere Sprachabdeckung, Audit, Aufbewahrung/Löschung
  und weitergehender Bot-Schutz bleiben offen. Keine vollständige Core-Abnahme.

### Commit für GitHub Desktop

Commit-Titel:

```text
feat: release NeoFab2 0.1.13 with registration and email account recovery
```

Commit-Beschreibung:

```text
Implement Core package 2: configurable registration, email activation and password reset.
Keep public account flows disabled by default; require SMTP, canonical origin and domain policy.
Add migration 0010_account_flows, pending status, single-use expiring codes and request limits.
Queue localized account emails atomically and prepare codes only in the mail worker.
Revoke codes and sessions on security changes; preserve local administrator recovery.
Add protected admin forms, shared button icons and account status guidance.
Validate 235 full-suite tests, then 42 focused account-flow tests including IDNA handling.
Build wheel/sdist and verify the installed wheel, migrations and documentation.
Preserve credential-ignore hardening; make audit and operational status package 3 next.
Keep testplugins at 0.1.0; no production migration, automatic commit or push.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.12 – 2026-09-19

Bereich: Core-Paket 1, SMTP und persistente Versandaufträge (S05, N05,
technische Teilumfänge S06/N01, S12, X05–X07). Zentrale Version **0.1.12**;
alle drei technischen Testplugins einschließlich CheckDesign bleiben **0.1.0**.

### Änderungen

- Administration → Systemeinstellungen → SMTP & Versandaufträge: validierte
  Einstellungen, Testauftrag, Statusliste mit Seitenwechsel und manuelle Wiederholung.
  Gemeinsame Button-Icons, englische Ausgangstexte und deutsche Übersetzungen.
- SMTP mit STARTTLS, direktem TLS oder lokalem Relay ohne Anmeldung. Zertifikats-
  und Hostnamenprüfung aktiv; Passwort ausschließlich in geschützter TOML-Datei.
  Keine Ausgabe von Nachrichtentexten, Passwörtern oder rohen SMTP-Fehlerantworten.
- Persistente Outbox mit Idempotenzschlüssel, atomarer Reservierung, Status und
  begrenzten Wiederholungen. Verwaiste bzw. mehrdeutige Übertragungen werden
  ungeklärt; erneuter Versand nur nach ausdrücklicher Bestätigung.
- Einmaliger CLI-Worker `mail-worker --limit 20`. SMTP-/Plugin-Deaktivierung
  pausiert neue Übernahmen; kein automatischer Scheduler installiert.
- Additiver Plugin-API-1-Vertrag `mail_permission` und `enqueue_email()` mit
  frischer Rechteprüfung und optional gemeinsamer Transaktion.
- [Betriebs- und Vertragsdokumentation](Core_SMTP_und_Versand.md), Funktionsmatrix,
  Setup/Schnellstart und Arbeitsplan aktualisiert. Nächster Punkt: Paket 2 mit
  Registrierung, Aktivierung und Self-Service-Passwort-Reset.
- Der vorher beauftragte Dokumentationsnachtrag zu Plugin-Verzeichnissen,
  Mindestlevel, ZIP-Bereitstellung und Deinstallation bleibt reine Planung
  ([P1–P5](Plugin_Pakete_und_Lifecycle.md)); keine Umsetzung dieser Pakete.

### Betrieb und Migration

Explizite Revision **`0009_mail_outbox`** nach `0008_core_files`, neue Tabelle
`core_mail_outbox`. Kein Schemaeingriff beim Start. Vor Update/Restore selbst
gestartete Worker bzw. Aufrufpläne stoppen; das vorhandene Update-Skript kennt
nur den Webdienst. Passende Datenbank-, Konfigurations- und Codesicherung erhalten.
Nach Restore SMTP vor dem nächsten Worker pausieren und mögliche bereits erfolgte
Zustellungen abgleichen. SMTP startet standardmäßig deaktiviert.

Unter `/etc/neofab2/config.toml` bei Bedarf `SMTP_PASSWORD` hinterlegen,
Webdienst und Worker neu starten. Als root, ausgeführt durch den Dienstbenutzer:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 mail-worker --limit 20
```

„Angenommen“ bestätigt die SMTP-Übernahme, nicht den Postfacheingang.
Keine Zusage exakt einmaliger Zustellung; keine automatische Outbox-Löschung.
Keine produktiven Daten, keine Nachrichten an reale Empfänger und kein altes
NeoFab verändert. Kontoverfahren aus S06/U02–U04 bleiben Paket 2.

### Prüfungen

- 28 Versandtests bestanden: Einstellungen/Rechte/CSRF, Geheimnisschutz,
  Header-/Größenvalidierung, Idempotenz/Rollback, Neustart, begrenzte Wiederholung,
  Plugin-Pause, parallele Reservierung, abgelaufene Übernahme, verspätetes Ergebnis,
  SMTP-Modi samt Hostnamenübergabe, Migration 0008 → 0009, Sicherung und CLI.
- Finale Gesamtsuite: **194 Tests bestanden** unter Windows/Python 3.12.
  Wheel und sdist 0.1.12 gebaut; separat installiertes Wheel einschließlich
  Migration, SMTP-Seite, pausiertem Worker und bisherigen Core-/Plugin-Seiten geprüft.
  120 relative Dokumentationslinks und `git diff --check` bestanden.
- Kein echter SMTP-Anbieter oder realer Postfacheingang geprüft. Visuelle
  Browserabnahme und Debian/LXC/systemd-Workerprüfung bleiben offen.
  Die vollständige Core-Abnahme ist nicht abgeschlossen.

### Commit für GitHub Desktop

Commit-Titel:

```text
feat: release NeoFab2 0.1.12 with SMTP settings and persistent mail queue
```

Commit-Beschreibung:

```text
Implement Core package 1: admin SMTP settings, queued test emails and mail status.
Add explicit migration 0009_mail_outbox, idempotent jobs, bounded retries,
exclusive worker claims and explicit handling of uncertain SMTP delivery.
Add the one-shot mail-worker CLI and permission-scoped plugin notification API.
Keep SMTP credentials in protected configuration; add shared icons and DE texts.
Document operation, migration, restore risks and remaining acceptance checks.
Preserve the planning-only plugin lifecycle packages P1-P5; make package 2 next.
Validate 194 tests, installed wheel, sdist and 120 relative documentation links.
Keep all testplugin versions at 0.1.0; no production migration or automatic commit.
```

Der Commit wird manuell in GitHub Desktop erstellt; kein Commit oder Push durch Codex.

## Version 0.1.11 – 2026-09-19

Bereich: ausdrücklich beauftragtes technisches Core-Testplugin CheckDesign
(S01, U07, N01, S12, X05/X06). Die zentrale Anwendungsversion ist **0.1.11**;
CheckDesign hat unabhängig davon die eigene Version **0.1.0**, Plugin-API 1.

### Änderungen

- Neues unabhängig aktivierbares Plugin `checkdesign`, Anzeigename **CheckDesign**,
  ohne Fachfunktion, Plugin-Abhängigkeiten oder eigene Tabellen.
- Auswahl als Hauptmenüpunkt ausschließlich für Mitarbeiter (`staff`) und
  Administratoren (`admin`). Normale Benutzer erhalten HTTP 403, Gäste werden
  zur Anmeldung weitergeleitet; Seiten und Stylesheet verwenden dieselbe Prüfung.
- Galerie für alle vorhandenen gemeinsamen Designelemente: Typografie, 15
  Farbvariablen, Flächen, Buttons/Links einschließlich deaktivierter Varianten,
  alle Icons, Formulare und Zustände, Meldungen/Badges, Tabellen, Navigation,
  Karten sowie gemeinsamer Kopf-/Fußbereich. Native Zusatzfelder sind gekennzeichnet.
- Eigene Hell-/Dunkel-Buttons mit Sonne-/Mond-Icon und aktivem Zustand.
  GET-Vorschauparameter gilt nur für die Plugin-Seite; keine Änderung an Profil,
  Systemeinstellungen oder anderen Sitzungen. Rückkehr zur regulären Darstellung
  über eigenen Link. Kein JavaScript erforderlich.
- Beispielfelder werden nicht gespeichert, ausgewählte Dateien weder gelesen
  noch hochgeladen. Themewechsel lädt die Seite neu und setzt Beispiele zurück.
- Gemeinsames Icon-Makro stellt seinen Bestand für die Galerie bereit;
  Plugin-Stylesheet ergänzt ausschließlich Galerieanordnung/Farbmuster.
  Core-Template besitzt einen Stylesheet-Erweiterungsblock.
- Deutsche Bedienungs-/Bereichsbezeichnungen, englische Ausgangstexte und
  Fallback. Vollständige Detail-/FR-Übersetzung bleibt offen.
- [CheckDesign-Anleitung](CheckDesign.md), Gestaltungsregeln, Paketierung und
  aktuelle Versionsangaben ergänzt. Paket 1 des Core-Plans bleibt unverändert
  als nächster offener Schritt eingeplant.

### Betrieb und Migration

**Keine neue Schema-Revision** gegenüber 0.1.10; weiterhin `0008_core_files`.
Normales Update nach manuellem Commit/Push gemäß [Setup](SETUP.md). CheckDesign
ist standardmäßig nicht aktiv; bestehende Auswahlen bleiben erhalten.
Als Administrator unter **Administration → Plugins** CheckDesign aktivieren und
alle Anwendungsprozesse kontrolliert neu starten. Danach können Mitarbeiter und
Admins den Menüpunkt **CheckDesign** öffnen. Deaktivierung sperrt nach Neustart
auch direkte Seiten-/Stylesheet-Aufrufe. Keine Produktivdaten verändert.

### Prüfungen

- **166 Tests bestanden** unter Windows/Python 3.12 (123,85 s).
- Sechs neue Plugin-Tests: Rollen und Navigation, geschützte Assets,
  Theme-/Sitzungsisolation, Kontodesign als Ausgangswert, keine Änderung von
  Konten/Systemeinstellungen, abgelehnte Theme-Werte, fehlender Schreibendpunkt,
  Aktivierung/Deaktivierung nach Neustart sowie Galerieprüfung in Hell/Dunkel.
- Gerenderte Galerie: eindeutige IDs, zugeordnete Labels/Hilfen, beschriftete
  Buttons mit dekorativen Icons, vollständiger Icon-/Farbbestand und CSP-Konformität.
- Wheel und sdist 0.1.11 gebaut; installiertes Wheel einschließlich
  CheckDesign-Seite, Vorschauwechsel, Icons und Plugin-Stylesheet geprüft.
- Interaktive visuelle Abnahme nicht durchgeführt: kein Browser verbunden.
  Kein eigener Debian-/LXC-Lauf, keine vollständige Core-Abnahme.

### Kopierbarer Commit-Text

```text
feat: release NeoFab2 0.1.11 with CheckDesign plugin 0.1.0

Add a staff/admin design gallery using shared UI components, colors and icons.
Preview light and dark themes locally without changing profile or system settings.
Keep sample controls read-only and protect plugin pages and assets by role.
Document activation, design checks and remaining visual acceptance.
Validation: 166 tests passed; wheel/sdist and installed plugin assets checked.
No schema change; no automatic commit or push.
```

## Version 0.1.10 – 2026-09-19

Bereich: Paket 0 des Core-Arbeitsplans und Administration (N01, U06, S10,
S01/S12, X05–X07).

### Änderungen

- Neuer Menüpunkt **Administration** mit berechtigungsabhängigen Buttons für
  Benutzerverwaltung, Plugins und Systemeinstellungen; die drei Einzelverweise
  entfallen in der Hauptnavigation. Zieladressen und Schutz bleiben erhalten.
- API 1 abwärtskompatibel um mehrere explizite Plugin-Rechte, einzelne
  Aktionsprüfungen und Besitzerprüfung erweitert. Kein Admin-Wildcard, `employee`
  bleibt `staff`. Ungültige/fremde/duplizierte Rechte werden zurückgewiesen.
- Öffentliche minimale Dateischnittstelle und getrennter technischer Dienst:
  modul- und besitzergebundene Uploads, Metadatenlisten und geschützte Downloads.
  Kontostatus wird erneut geprüft; CSRF, Dateinamen-/Typ-/Größenlimits und
  ausschließliche Anhang-Auslieferung mit `nosniff`/`no-store` bleiben verbindlich.
- Bestehendes Verwaltungs-Testplugin nutzt TXT-Dateien bis 256 KiB: Benutzer
  lesen eigene, Mitarbeiter/Administratoren alle Dateien dieses Testplugins.
  Nur Mitarbeiter/Administratoren dürfen die separate Formularprüfung ausführen.
  Core-Plugin-Verwaltung bleibt ausschließlich administrativ.
- Dateien und Metadaten werden für diesen Minimalumfang atomar als SQLite-BLOB
  gespeichert. Keine benutzergesteuerten Ablagepfade; bestehende Datenbanksicherung
  umfasst Testdateien. Keine automatische Löschung bei Deaktivierung.
- Deutsche [Bedienungs-/Vertragsanleitung](Core_Dateien_und_Rechte.md),
  Gestaltungsregeln, Versionsangaben und Core-Arbeitsplan aktualisiert.
  Paket 1 (SMTP/Versandaufträge/Worker) ist als nächster Schritt eingeplant.

### Betrieb und Migration

Explizite Revision **`0008_core_files`**, Vorgänger `0007_user_options`.
Leere Tabelle mit Modul, Besitzer-Fremdschlüssel, Dateiname, Größe, Zeit und Inhalt;
keine Bestandsdatenübernahme. Normales Update nach manuellem Commit/Push über
`script/upDateNeoFabService`, einschließlich Sicherung und expliziter Migration.
Erwartet: Version 0.1.10 und `Database and schema ready.`. Keine Migration beim
App-Start. Default weiterhin keine aktiven Plugins; gespeicherte Aktivierungen
bleiben bestehen. Ist das Verwaltungs-Testplugin bereits aktiv, erhalten Benutzer
und Mitarbeiter nach Update Zugriff auf dessen synthetische Testdateiseite.

Die SQLite-Ablage ist bewusst auf kleine Anhänge begrenzt (Vertrag maximal 1 MiB,
Testplugin 256 KiB, HTTP-Limit 1 MiB inklusive Multipart-Overhead). Große Dateien,
fachliche Objektbindung, Inhaltsprüfung, Viewer, Löschung/Kontingente, Versand
und Rollenpflege sind nicht Bestandteil dieses Pakets. Keine Fachplugins,
Produktivmigration oder vollständige Core-Abnahme.

### Prüfungen

- **160 Tests bestanden** unter Windows/Python 3.12 (112,87 s), davon 27 neue
  Fälle zu Plugin-Rechten, Besitzerprüfung, Upload-/Download-Schutz, Dateirichtlinien,
  Grenzen, Rechtewiderruf, Administration und Migration von 0.1.9.
- Neustart-Persistenz, gesperrte Routen/Aufgaben nach Deaktivierung, erhaltene
  Dateien, SQLite-Sicherung mit Inhalt sowie wiederholbares Upgrade mit
  unveränderten Konten geprüft. Ausschließlich synthetische Daten.
- Wheel und sdist 0.1.10 gebaut; separat installiertes Wheel mit Migration,
  Templates, CSS und Logo geprüft. Zusätzliche Paketprüfung von Administration,
  Icons und Upload/Download bestanden. Temporäres Windows-Verzeichnis beim
  Zusatzlauf blockiert; Wiederholung mit explizitem Projektpfad erfolgreich.
- `git diff --check` ohne Befund.
- Bestehende Tests auf den neuen Administrationseinstieg und `core_files`
  angepasst; lange parametrisierte Testnamen für Windows verkürzt.
- Interaktive Browser- und echter Debian-/LXC-Lauf nicht durchgeführt.
  Kein Commit oder Push ausgeführt.

### Kopierbarer Commit-Text

```text
feat: release 0.1.10 with administration and plugin permission/file contracts

Group user, plugin and system management under Administration.
Extend API 1 with explicit permissions, ownership checks and small-file services.
Exercise protected uploads/downloads through the synthetic management test plugin.
Add explicit migration 0008_core_files; preserve existing accounts and data.
Document package 0 completion, operating limits and SMTP as the next core step.
Validation: 160 tests passed; wheel/sdist built and installed wheel checked.
Interactive browser and Debian/LXC acceptance remain open.
```

## Version 0.1.9 – 2026-09-19

Bereich: Benutzerverwaltung, Navigation und gemeinsame Gestaltung
(U05, S01, S04, S12, X05/X06).

### Änderungen

- Stammdaten-Direktlinks aus Benutzerliste und Benutzerformularen entfernt.
- Systemeinstellungen öffnen Stammdaten über einen sekundären Button mit Icon.
- Alle vorhandenen Buttons einschließlich Login, Sprachwahl, Profil,
  Plugin-Verwaltung und Testplugin erhalten passende dekorative SVG-Icons
  zusätzlich zur sichtbaren Beschriftung. Aktivierung/Deaktivierung verwenden
  unterschiedliche Icons. Gemeinsames Makro ohne externe Ressourcen.
- Einheitliche Icongröße, Abstände, Mindesthöhe 44 px und Hover-/Aktiv-/
  Deaktiviert-Zustände im gemeinsamen CSS; sekundäre Link-Buttons unterstützt.
- Deutsche [UI-Gestaltungsregeln](UI_Gestaltungsregeln.md) mit Beispielen,
  Semantik, Barrierefreiheit, Formularen, Tabellen und Prüfanleitung ergänzt.
  Bedienungsanleitungen und aktuelle Versionsangaben aktualisiert.

### Prüfungen

- 133 bestehende Tests unter Windows bestanden (86,33 s), ausgeführt mit
  `.venv/Scripts/python.exe -m pytest -q --basetemp .test-artifacts/pytest019`.
- Erster Lauf wegen fehlendem Zugriff auf das allgemeine Windows-Pytest-
  Temp-Verzeichnis abgebrochen; mit projektspezifischem Temp-Pfad erfolgreich.
- Zusätzliche HTML-Prüfung mit synthetischem Admin: 14 gerenderte Seiten,
  28 Buttons mit sichtbarem Text und dekorativem SVG samt nichtleerem Pfad;
  Benutzerliste und beide Benutzerformulare ohne Stammdaten-Verwaltungslinks,
  Stammdaten-Einstieg in den Einstellungen als Button.
- Interaktive visuelle Prüfung nicht durchgeführt: kein Browser verbunden.
  Keine neue vollständige Core- oder LXC-Abnahme.
- `git diff --check` ohne Befund.

### Betrieb und Migration

Keine neue Schema-Revision; gegenüber 0.1.8 keine Datenmigration. Bestehende
Auswahllisten, Rechte und CSRF-Schutz bleiben erhalten. Reguläres Update nach
manuellem Commit/Push gemäß [Skriptübersicht](../script/README.md) und
[Setup](SETUP.md); bei älteren Ständen weiterhin explizite Migrationen ausführen.
Erwartete Anwendungs-/Footer-Version: 0.1.9. Bei veraltetem Aussehen Browsercache
neu laden. Kein automatischer Commit/Push und keine Produktivdaten verändert.

### Kopierbarer Commit-Text

```text
feat: release 0.1.9 with consistent button icons and master data navigation

Remove master data links from user management and user forms.
Style the system settings entry as a button and add shared SVG icons to all buttons.
Document UI design rules and update version references and implementation evidence.
Validation: 133 tests passed; rendered HTML checked on 14 pages.
No schema change; interactive browser verification remains open.
```

## Version 0.1.8 – 2026-09-19

Bereich: Betriebsskripte, Formularhilfen und verwaltete Benutzer-Auswahllisten
(X01–X07, U05, S01/S02, S04, S12).

### Änderungen

- Nachbesserung vom 2026-09-19, weiterhin 0.1.8: Einstieg **System settings →
  Master data** mit separaten Zielseiten für Positionen, Studiengänge und
  Kostenstellen. Bereits vorhandene Anlage-/Änderungsformulare bleiben erhalten.
  Zusätzliche Trennlinien bei Abschlussprüfung/Bereitschaft; tatsächliche
  IP-Adressen auch beim Teststart, Diagnosehinweis statt IP-Platzhalter.
  Keine zusätzliche Schemaänderung. Beim Update aus 0.1.7 war noch der alte
  Skriptcode geladen; neue Ausgabe ab erneutem Aufruf der aktualisierten Skripte.

  Kopierbarer Commit-Titel: `fix: clarify maintenance output and expose master data settings`

  Beschreibung: `Add a master data overview under system settings, link separate
  option forms, separate maintenance checks visually and display detected IP URLs.`

  Prüfung der Nachbesserung: 133 Tests bestanden; ergänzte Zugriffsschutzprüfung
  anschließend mit 8 Benutzerlisten-Tests erneut bestanden. Alle fünf Shell-Dateien
  bestehen `bash -n`, `git diff --check` ohne Befund. OS-Kommandos simuliert;
  neue Darstellung noch nicht selbst im Browser oder Debian-LXC geprüft.

- Installation, Service-Einrichtung, Update und Notfall-Passwort-Reset geben zum
  Abschluss einen eingerahmten Zusammenfassungsblock aus: Ergebnis/Exit-Code,
  IP-Adressen und interner Port, Servicezustand, Pfade, installierte Version,
  Admin-E-Mails, Sicherungspfad und kopierbare Wartungs-/Diagnosebefehle.
- Erfolgs-, Abbruch- und Fehlerfälle sowie bereits aktueller Git-Stand werden
  unterschieden. Der ursprüngliche Exit-Code bleibt erhalten. Ein Fehler des
  optionalen Installationstests wird nicht als fehlgeschlagene Basisinstallation
  ausgegeben; unvollständige Sicherungen bleiben ausdrücklich gekennzeichnet.
- Neuer lesender CLI-Befehl `maintenance-info` liefert Version, HTTP-/HTTPS-Hinweis
  und Admin-E-Mails ohne Plugin-Start, Passwörter, Hashes oder andere Secrets.
- Kurze englische Hilfetexte für Login, Sprachwahl, Profil/Passwortwechsel,
  Benutzerformulare, Systemeinstellungen und die neuen Listenformulare.
  `aria-describedby` verknüpft die Eingaben mit den Hilfen; `_()` bereitet
  spätere Übersetzungen vor. Neue DE-/FR-Hilfetexte sind noch nicht enthalten.
- Position, Studiengang und Kostenstelle sind optionale Auswahlfelder.
  Administratoren pflegen jede Liste über eine eigene Backend-Seite unter
  **User management**. Anlegen, Umbenennen und Aktivieren/Deaktivieren sind
  implementiert; Änderungen werden in der Datenbank gespeichert.
- Kontospeicherung prüft Auswahlwerte und Rechte innerhalb derselben Transaktion.
  Unbekannte, listenfremde oder neu zugeordnete inaktive Werte werden abgewiesen.
  Umbenennen aktualisiert vorhandene Zuordnungen atomar; Deaktivieren erhält sie.
- Version und deutsche Betriebs-/Bedienungsanleitungen aktualisiert.

### Betrieb und Schema

Die explizite Schema-Revision `0007_user_options` legt die leere Tabelle
`core_user_options` an. **Auf Benutzerwunsch keine Übernahme alter Freitextwerte**,
keine Vorbelegung und keine fachliche Datenmigration. Neue Listen im Backend
selbst pflegen. Die vorhandenen Textspalten der Benutzer werden weiterverwendet
und gegen die Listen validiert; keine Änderung vorhandener Hashes oder Sitzungen.
Alte Freitexte erscheinen nicht als Auswahl; beim nächsten Speichern im Formular
gilt die gewählte Option bzw. der leere Wert. Keine automatische Schemaänderung
beim App-Start. Update über das reguläre Skript mit Sicherung.

Die Kostenstellenliste ist eine organisatorische Benutzerangabe, keine
Kostenstellen-/Finanzverwaltung eines Fachplugins. Löschen von Listeneinträgen
ist nicht enthalten; zum Ausblenden deaktivieren.

Die Zusammenfassung nennt interne HTTP-Adressen, deren externe Erreichbarkeit
nicht geprüft ist. Bei Secure-Cookies muss weiterhin die selbst konfigurierte
HTTPS-Adresse verwendet werden; die Skripte richten kein TLS ein. Fehlende
Zusatzinformationen ändern den Erfolg/Fehler des eigentlichen Skripts nicht.
Details: `script/README.md`, `doku/SETUP.md`, `doku/Core_Auswahllisten.md`.

### Prüfungen

- 132 Tests unter Windows/Python 3.12 bestanden. Neue Nachweise: getrennte
  Listenformulare, Persistenz nach Neustart, Rechte/CSRF, Feldgrenzen, Duplikate,
  HTML-Maskierung, atomare Umbenennung und Fehlerspeicherung, inaktive/fremde
  Auswahlwerte sowie leere Listen nach Upgrade ohne Freitextübernahme.
- Feldhilfen an allen sichtbaren Eingabefeldern der betroffenen Formulare per
  HTML-Prüfung nachgewiesen; Übersetzbarkeit mit synthetischem Katalogeintrag geprüft.
- Skript-Zusammenfassungen mit simulierten Betriebssystembefehlen einschließlich
  Fehler/Abbruch, IPv4/IPv6, fehlenden Metadaten, optionalem Teststart und Update-
  Fehlern geprüft. Lesender CLI-Abruf verändert keine Daten und gibt keine Secrets aus.
- Bash-Syntax aller fünf Shell-Dateien geprüft; 69 lokale Dokumentationslinks und
  `git diff --check` ohne Befund. Kein eigener ShellCheck-Lauf für diesen Stand.
- Wheel und sdist 0.1.8 gebaut; separat installiertes Wheel mit Migration,
  Listenformularen/-speicherung, Core-/Plugin-Templates, CSS und Logo geprüft.
- Kein echter Debian-/LXC-/systemd-Lauf und keine interaktive Browserabnahme.
  Nur synthetische Testdaten; keine vollständige Core-Abnahme, kein Commit/Push.

### Commit für GitHub Desktop

```text
0.1.8: Skript-Zusammenfassungen, Feldhilfen und Benutzer-Auswahllisten ergänzen
```

```text
Abschlussübersichten für Installation, Service, Update und Admin-Passwort-Reset ergänzen.
Lesende Versions-/Admin-Informationen ohne Secrets über maintenance-info bereitstellen.
Englische übersetzbare Feldhilfen mit aria-describedby einbinden.
Positionen, Studiengänge und Kostenstellen über eigene Admin-Formulare pflegen.
Benutzer-Auswahlwerte transaktional prüfen; Umbenennen und Deaktivieren unterstützen.
Schema 0007_user_options mit leeren Listen anlegen, ohne alte Freitexte zu übernehmen.
132 Tests, Bash-Syntax, Dokumentationslinks, Paketbau und installiertes Wheel geprüft.
Deutsche Anleitungen und Funktionsnachweise aktualisieren; Container-/Browserabnahme offen.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.7 – 2026-09-18

Bereich: englische Ausgangssprache, Übersetzungsschlüssel und Core-Arbeitsplan
(S02/U07, S01, U05, S04, N01, S12, X05–X07).

### Änderungen

- Englische Ausgangstexte in Core-Oberfläche, Administration, Testplugins,
  Validierungs-/Zugangsmeldungen und CLI. Englische Schlüssel in `MESSAGES`;
  Deutsch wird wie Französisch als Übersetzung behandelt.
- Englisch als Standard für Gäste ohne Auswahl, neue Konten und fehlende
  Übersetzungen/ungültige gespeicherte Sprachcodes. Bestehende Kontosprachen
  und bisherige französische Übersetzungen bleiben erhalten.
- Bisher fest deutsche Admin- und Testplugin-Texte für Übersetzung markiert.
  Platzhalter bleiben HTML-maskiert; technische Formularwerte bleiben unverändert.
- Neue öffentliche Standardtexte sind englisch. Individuelle Einstellungen und
  Benutzerinhalte werden nicht automatisch übersetzt oder überschrieben.
- Priorisierter Core-Plan mit Funktions-IDs und Abnahmekriterien in
  `doku/Core_Naechste_Schritte.md`: zunächst Versanddienst/persistente Aufgaben,
  dann E-Mail-Kontoverfahren, Audit, übrige Core-Dienste, Import und Betriebsabnahme.
  Diese Schritte sind geplant, nicht in 0.1.7 implementiert.
- Version 0.1.7, deutsche Anleitungen und Umsetzungsnachweis aktualisiert.

### Betrieb und Migration

`0006_english_default` setzt den Datenbank-Standard für neue Konten auf `en`.
SQLite baut die Benutzertabelle explizit über Alembic neu auf. Kontosprachen,
Hashes, Zusatzfelder und Einstellungen bleiben erhalten; bestehende Sitzungen
werden während des Tabellenumbaus gegen die vorhandene CASCADE-Regel gesichert
und innerhalb derselben Transaktion wiederhergestellt. E-Mail-Eindeutigkeit und
Fremdschlüsselkonsistenz sind geprüft. Reguläres Update-Skript mit Sicherung
verwenden; keine Migration beim Webstart.

Bestehende deutsche Konten können unter **Mein Profil → Sprache → English**
umgestellt werden. Benutzerdefinierte deutsche Startseitentexte bei Bedarf in
**System settings** bearbeiten. Shell-Betriebsskripte und Anleitungen bleiben
deutsch; CLI-Ausgaben sind englisch. Siehe `doku/Core_Sprachen.md`.

Französische Admin-/Plugin-Texte und einzelne dynamische technische Diagnosen
verwenden weiterhin englischen Fallback; eigene Plugin-Kataloge folgen später.
Keine produktiven Daten verändert, keine Fachplugins hinzugefügt. Keine vollständige
S02- oder Core-Abnahme; interaktive Browser- und Container-Abnahme stehen aus.

### Prüfungen

- 117 Tests unter Windows/Python 3.12 bestanden: Anmeldung, Rechte, CSRF,
  Benutzerverwaltung, Sprachwahl/-persistenz, Fallback, HTML-Maskierung,
  englische Core-/Admin-/Testplugin-Seiten, Migrationen und Betriebssteuerung.
- Nach abschließenden Ergänzungen 10 Sprach-/Migrationstests einschließlich
  Sitzungserhaltung sowie 16 Plugin-/Admin-CLI-Tests erneut bestanden.
- Wheel und sdist 0.1.7 gebaut; separat installiertes Wheel aus neutralem
  Verzeichnis mit Migration, Core-/Plugin-Templates, CSS, Logo und Plugin-Neustart
  geprüft. CLI meldet 0.1.7 und englische Hilfe. `git diff --check` ohne Befund.
- Tests ausschließlich mit synthetischen Daten. Temporäres Testverzeichnis im
  Repository, da das vorhandene Windows-pytest-Tempverzeichnis gesperrt war.
- Kein eigener LXC-/systemd-Lauf, kein interaktiver Browsertest, kein Commit/Push.

### Commit für GitHub Desktop

```text
0.1.7: Englisch als Ausgangssprache und Core-Fahrplan ergänzen
```

```text
Core-Oberfläche, Administration, Testplugins und CLI auf englische Ausgangstexte umstellen.
Englische Übersetzungsschlüssel und Fallback verwenden; Deutsch als Übersetzung erhalten.
Migration 0006_english_default für neue Konten ergänzen und bestehende Kontodaten sowie Sitzungen erhalten.
Core-Fahrplan mit priorisierten Paketen, Funktions-IDs und Abnahmekriterien dokumentieren.
117 Tests sowie abschließende gezielte Prüfungen, Paketbau und installiertes Wheel geprüft.
Deutsche Betriebsanleitungen, Versionshistorie und Funktionsnachweise aktualisieren.
Französische Ergänzungen, Container-/Browserprüfung und vollständige Core-Abnahme bleiben offen.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.6 – 2026-09-18

Bereich: Benutzerformulare und Sprachwahl (U05, S02/U07, X05–X07).

### Änderungen

- Sprachwahl Deutsch/Englisch/Französisch für Navigation, Login, Profil,
  Passwortwechsel und zentrale Zugangsfehlermeldungen.
- Gast-Sprachwahl per CSRF-geschütztem POST; dauerhafte Kontosprache im Profil.
  Kontosprache hat nach Anmeldung Vorrang. Abmeldung und Passwortwechsel erhalten
  die Sprache für die Anmeldeseite.
- Deutsche Ausgangstexte als Fallback; unbekannte Sprachcodes beim Speichern
  abweisen. Übersetzungstexte weiterhin HTML-maskiert.
- Zentrale Version 0.1.6 und Arbeitsstand dokumentiert. Nutzer bestätigt 0.1.5.
- Beide Benutzerformulare um Anrede, Vorname, Nachname, Adresse, Position,
  Kostenstelle als Freitext, Studiengang und administrative Notiz ergänzt.
- Sprache und Aktivstatus auch beim Anlegen setzen; optionales neues Passwort
  beim Bearbeiten mit Wiederholung. Leere Passwortfelder erhalten den bisherigen Hash.
- Alle Admin-Änderungen atomar; Passwortänderung widerruft Sitzungen.
  Private Zusatzdaten werden nicht in den allgemeinen Auth-Kontext geladen.

### Betrieb und Migration

Explizite Migration `0004_user_locale` ergänzt die Kontosprache mit Standard `de`.
`0005_user_details` ergänzt leere optionale Zusatzfelder. Bestehende Konten,
Hashes und Darstellung bleiben erhalten. Update über das reguläre Skript.
Sprachabdeckung
für weitere Admin-Seiten, Startseiten- und Plugin-Inhalte steht noch aus;
keine vollständige S02- oder Core-Abnahme. Details: `doku/Core_Sprachen.md`
und `doku/Benutzerverwaltung.md`. Aktivierungslink-Versand bleibt dem E-Mail-Schritt
vorbehalten. Es wurden keine Daten aus NeoFab oder dem Screenshot übernommen.

### Prüfungen

- 114 Tests unter Windows/Python 3.12 bestanden, darunter Gast-/Kontosprache,
  Vorrang und Persistenz, CSRF, deutsche Rückfalltexte, Maskierung und Upgrade
  vom bisherigen Schema mit Erhalt der Bestandswerte, beide Benutzerformulare,
  Feldgrenzen, private Notizen, Passwortwechsel und Schutz des letzten Admins.
- Wheel und sdist 0.1.6 gebaut; installiertes Wheel mit Migration und vorhandenem
  Core-/Plugin-Smoke-Test geprüft. CLI meldet 0.1.6.
- Keine Container- oder interaktive Browserprüfung. Kein Commit oder Push.

### Commit für GitHub Desktop

```text
0.1.6: Benutzerformulare erweitern und Sprachwahl ergänzen
```

```text
Deutsch, Englisch und Französisch für Navigation, Login und Profil ergänzen.
Kontosprache mit Migration 0004_user_locale dauerhaft speichern.
Benutzerformulare um Kontakt-/Organisationsangaben, Notiz und Sprache ergänzen.
Migration 0005_user_details erhält bestehende Konten und legt leere Zusatzfelder an.
Optionalen Admin-Passwortwechsel mit Wiederholung und Sitzungswiderruf umsetzen.
Gast-Sprachwahl, Vorrang der Kontosprache und deutschen Fallback prüfen.
114 Tests sowie Paketbau und Prüfung des installierten Wheels bestanden.
Dokumentation und Umsetzungsnachweise aktualisieren; Container-Abnahme noch offen.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.5 – 2026-09-17

Bereich: Plugin-Verwaltung im Backend, Neustartablauf und zweites Testplugin
(N01, U06, S01/S12, X05/X06).

### Änderungen

- Aktivierung/Deaktivierung unter `/admin/plugins` als gewünschte Auswahl vormerken.
  Eigenes Admin-Recht `core.plugins.manage`, POST/CSRF und erneute Rechteprüfung
  innerhalb der Speichertransaktion.
- Persistenter Zielzustand in `core_settings`; vorhandene TOML-Auswahl gilt bis
  zur ersten Backend-Speicherung. Danach hat die Datenbank Vorrang, auch bei `[]`.
- Anzeige des laufenden Webprozesses getrennt von gespeicherter Auswahl;
  Neustarthinweis bei Abweichung. Kein automatischer Container-/Dienstneustart.
- Abhängigkeiten vor Speicherung validieren; benötigte Plugins nicht einzeln
  deaktivierbar. Parallele Aktionen arbeiten auf dem aktuellen Datenbankstand.
- Neues synthetisches `management_test` 0.1.0 (API 1), abhängig von `core_test`
  ab 0.1.0. Eigene Testseite, CSRF-geschütztes Testformular und lokale Testaufgabe.
  Das bestehende Core-Testplugin bleibt Version 0.1.0.
- Lokale bestätigte Wiederherstellung `plugins-restore-config` übernimmt eine
  geprüfte TOML-Auswahl, falls die gespeicherte Auswahl den Start verhindert.
- Update-/Prüfanleitungen, Versionsangaben und Funktionsnachweise aktualisiert.
  Nutzer meldet den vorherigen Schritt 0.1.4 als lauffähig.

### Betrieb und Migration

Reguläres Update mit `script/upDateNeoFabService`, keine neue Schema-Revision
gegenüber 0.1.4. Neue Plugin-Auswahl wird mit der Datenbank gesichert; keine
Plugin-Deinstallation oder Datenlöschung. Das neue Testplugin wird nicht automatisch
aktiviert. Erst `core_test`, dann `management_test` im Backend vormerken, danach
startet der **Proxmox-Admin den Container manuell neu**. Zur Deaktivierung die
umgekehrte Reihenfolge verwenden. Bis zum Neustart behalten laufende Prozesse
ihre bisherige Registrierung. Frisch gestartete CLI-/Webprozesse übernehmen
den Zielzustand bereits bei ihrem eigenen Start. Die Übersicht bestätigt
ausdrücklich nur den Zustand des antwortenden Webprozesses.

Anleitung, Fehlersuche und Wiederherstellung: `doku/plugin-development.md`.
Keine produktiven Fachplugins; persistente Aufgaben, weitere technische Dienste,
Sprachübersetzungen und vollständige Core-Abnahme bleiben offen.

### Prüfungen

- 95 Tests unter Windows/Python 3.12 bestanden, darunter 11 neue Fälle für
  Zielzustand/Neustart, Abhängigkeiten, CSRF/Rechte, Parallelität, TOML-Übernahme,
  Abbruch bei ungültiger Auswahl und lokale Wiederherstellung.
- Wheel und sdist 0.1.5 gebaut; installiertes Wheel mit Backend-Aktivierung,
  erneutem App-Start, zweiter Plugin-Vorlage und Testaufgabe geprüft.
- CLI meldet 0.1.5; lokale Dokumentationslinks und `git diff --check` geprüft.
- Keine Änderungen an Shell-Skripten. Kein eigener Proxmox-Neustart, keine
  interaktive Browserprüfung und keine Linux-CI dieses Schritts ausgeführt.

### Commit für GitHub Desktop

Commit-Titel:

```text
0.1.5: Plugin-Verwaltung im Backend und zweites Testplugin ergänzen
```

Commit-Beschreibung:

```text
Plugin-Aktivierung und Deaktivierung im Backend mit Admin-Recht und CSRF ergänzen.
Zielzustand transaktional speichern und vom laufenden Prozesszustand unterscheiden.
TOML-Auswahl bis zur ersten Backend-Speicherung als Ausgangswert erhalten.
Abhängigkeiten vor Speicherung prüfen und parallele Änderungen erhalten.
Neustarthinweis für manuellen Container-Neustart durch Proxmox-Admin anzeigen.
Abhängiges Verwaltungs-Testplugin mit Formular und lokaler Testaufgabe ergänzen.
Lokale Wiederherstellung der Plugin-Auswahl und deutsche Prüfanleitung bereitstellen.
95 Tests und Prüfung des installierten Pakets bestanden; keine neue Schema-Revision.
Version 0.1.5 und Funktionsnachweise aktualisieren; Proxmox-Abnahme noch offen.
```

Der Commit wird manuell in GitHub Desktop erstellt. Kein Commit oder Push durch Codex.

## Version 0.1.4 – 2026-09-17

Bereich: Core-Systemeinstellungen und Darstellung (S04, S01, U07, X05–X07).

### Änderungen

- Admin-Seite `/admin/settings` für Werkstattname, Kurzbeschreibung,
  Begrüßungstext und Standarddarstellung Hell/Dunkel.
- Vier ausdrücklich freigegebene öffentliche Werte in `core_settings`;
  serverseitige Validierung, transaktionale Speicherung und erneute Rechteprüfung.
  Keine Secrets oder fremden Einstellungsschlüssel im Formular.
- Startseite und Kopfzeile verwenden gespeicherte Angaben mit HTML-Maskierung.
  Änderungen wirken ab der nächsten Anfrage ohne Dienstneustart.
- Persönliche Darstellung Hell/Dunkel/Systemvorgabe unter `/profile`, dauerhaft
  im Konto gespeichert. Gemeinsame CSS-Farben gelten für Core und Testplugin.
- Deutsche Bedienungs-/Updateanleitung und Umsetzungsnachweise ergänzt;
  Nutzer meldet vorherigen Schritt 0.1.3 als erfolgreich getestet.

### Betrieb und Migration

Das reguläre Update-Skript erstellt Sicherungen und führt `0003_user_theme`
nach `0002_core_users` aus. Vorhandene Konten erhalten `system` und folgen
zunächst der unveränderten dunklen Standarddarstellung. Benutzer, Passwort-Hashes,
Sitzungen und Einstellungen bleiben erhalten. Keine automatische Schemaänderung
beim Start oder Seitenaufruf. Cookie-Konfiguration und Plugin-Aktivierung bleiben
unverändert. Anleitung: `doku/Core_Einstellungen.md`.

Sprachübersetzungen, Einstellungsimport/-export, SMTP, Impressum/Datenschutz und
weitere Core-Dienste bleiben offen. Keine vollständige Core-Abnahme.

### Prüfungen

- 84 Tests unter Windows/Python 3.12 bestanden: Rechte/CSRF, Eingabegrenzen,
  Maskierung, Isolation fremder Einstellungen/Konten, dauerhafte Speicherung,
  persönliche Darstellung und Migration vom 0.1.3-Schema mit Datenerhalt.
- Wheel und sdist 0.1.4 gebaut. Installiertes Wheel mit Migration, Login,
  Profil, Benutzer-/Plugin-/Einstellungsseiten, Testplugin und hellem Layout geprüft.
- CLI meldet 0.1.4; Git-Diff und lokale Dokumentationslinks geprüft.
- Kein Browser verbunden: keine interaktive visuelle Prüfung. Eigener LXC-Test
  dieses Schritts und Linux-CI nicht ausgeführt. Shell-Skripte unverändert.

### Commit für GitHub Desktop

Commit-Titel:

```text
0.1.4: Systemeinstellungen und persönliche Darstellung ergänzen
```

Commit-Beschreibung:

```text
Admin-Einstellungen für Werkstattname, Begrüßung und Standarddarstellung einführen.
Öffentliche Angaben validieren, maskieren und transaktional speichern.
Persönliche helle/dunkle Darstellung mit Systemvorgabe im Profil ergänzen.
Migration 0003_user_theme mit Erhalt bestehender Konten und Einstellungen hinzufügen.
Gemeinsame CSS-Farben für Core und Testplugin verwenden.
84 Tests sowie Paketbau und Prüfung des installierten Wheels bestanden.
Version 0.1.4, Betriebsanleitungen und Funktionsnachweise aktualisieren.
Interaktive Browserprüfung und Container-Abnahme dieses Schritts noch offen.
```

Der Commit wird manuell in GitHub Desktop erstellt. Kein Commit oder Push durch Codex.

## Version 0.1.3 – 2026-09-17

Bereich: Core-Plugin-Vertrag und synthetisches Testplugin (N01, U06, S01,
S12, X05/X06); bestätigter Container-Zugang (U01/U07).

### Änderungen

- Plugin-API 1 mit Kennung, Version, API-Version, explizitem Zugriffsrecht,
  Rollen, Blueprint-Factory, Mindestversionen von Abhängigkeiten und lokalen Aufgaben.
- Prüfung auf fehlende/zu alte Abhängigkeiten, Zyklen, doppelte Kennungen und
  inkompatible aktive API; Fehler verhindern den Start.
- Gemeinsame Navigation und serverseitiger Zugriffsschutz; kein pauschales
  Administratorrecht auf alle Plugins. Zentrale CSRF-Prüfung bleibt aktiv.
- Admin-Übersicht `/admin/plugins` zeigt Versionen, API, Status und Abhängigkeiten.
- Synthetisches `core_test` 0.1.0 mit eigener Vorlage und lokaler Testaufgabe;
  standardmäßig deaktiviert. Keine Fachfunktion und keine neuen Tabellen.
- CLI `plugin-task` führt nur Aufgaben aktivierter Plugins aus.
- Anleitung für Aktivierung, Deaktivierung, Ergebnisprüfung und Fehlerhilfe ergänzt.
- Anmeldung und Passwortwechsel im HTTP-Container vom Nutzer bestätigt:
  Secure-Cookie bei HTTP war die Ursache, Korrektur auf `false` erfolgreich.

### Betrieb und Migration

Reguläres Update mit `script/upDateNeoFabService`; keine neue Schema-Revision.
Bestehende Daten, Konten und Cookie-Konfiguration bleiben erhalten. Standard:
`ENABLED_PLUGINS = []`. Zur Prüfung ausdrücklich `["core_test"]` setzen,
`neofab2 check` ausführen und alle Web-/Aufgabenprozesse neu starten.
Deaktivierung entfernt keine Daten; direkter Zugriff liefert danach 404 und
lokale Aufgaben werden abgewiesen. Anleitung: `doku/plugin-development.md`.

API 1 umfasst ein Zugriffsrecht je Plugin und lokale Aufgaben ohne Scheduler.
Plugin-Einstellungen, persistente Jobs und weitere technische Dienstverträge
bleiben offen. Sprache/Design, E-Mail-Verfahren und Benutzerimport sind weiterhin
offen; keine vollständige Core-Abnahme und keine produktiven Fachplugins.

### Prüfungen

- 73 Tests unter Windows/Python 3.12 bestanden, einschließlich 14 neuer
  Plugin-Vertragstests zu Rechten, CSRF, Abhängigkeiten, Aufgaben und Deaktivierung.
- Nach Kapselung der Plugin-Vorlage erneut alle 14 Plugin-Tests bestanden.
- Wheel und sdist 0.1.3 gebaut; installiertes Wheel mit Migration, Anmeldung,
  Profil, Benutzer-/Plugin-Übersicht, Plugin-Vorlage und Testaufgabe geprüft.
- CLI meldet Version 0.1.3; Git-Diff auf Formatfehler geprüft.
- Keine Änderungen an Shell-Skripten. Kein eigener LXC-Test des neuen Plugin-Schritts,
  keine ausgeführte Linux-CI oder interaktive Browserprüfung.

### Commit für GitHub Desktop

Commit-Titel:

```text
0.1.3: Plugin-Vertrag und geschütztes Core-Testplugin ergänzen
```

Commit-Beschreibung:

```text
Plugin-API 1 mit Versionen, Abhängigkeiten, Rechten und lokalen Aufgaben einführen.
Plugin-Navigation, Admin-Übersicht und synthetisches Core-Testplugin ergänzen.
Aktivierung per Konfiguration und Neustart; deaktivierte Seiten und Aufgaben sperren.
Fehlende, inkompatible und zyklische Abhängigkeiten beim Start ablehnen.
73 Tests sowie Paketbau und Prüfung des installierten Wheels bestanden.
Version, Betriebsanleitungen und Funktionsnachweise aktualisieren.
Bestätigten HTTP-Login und Passwortwechsel dokumentieren.
Keine neue Schema-Revision; weitere Core-Dienste und LXC-Plugin-Abnahme offen.
```

Der Commit wird manuell in GitHub Desktop erstellt. Kein Commit oder Push durch Codex.

## Version 0.1.2 – 2026-09-17

Bereich: Core-Benutzerzugang / Installation und Wiederherstellung (U01,
U05–U08, S01, S12, X01, X04–X07).

### Änderungen

- Anmeldung und POST-Abmeldung mit scrypt-Passwort-Hashing, CSRF-Schutz,
  serverseitig widerrufbaren Sitzungen und Anmeldebegrenzung.
- Benutzer anlegen, bearbeiten, aktivieren und deaktivieren; Rollen Benutzer,
  Mitarbeiter und Administrator mit serverseitigen Rechteprüfungen.
- Eigenes Profil, Passwortwechsel und Schutz des letzten aktiven Administrators
  einschließlich paralleler Änderungen.
- Ersten Administrator per CLI anlegen; Notfallskript `resetAdminPassword`
  mit verdeckter Eingabe, Admin-Auswahl und ausdrücklicher Reaktivierung.
- Installer um Erstadmin und HTTPS-/HTTP-Testauswahl ergänzt. Arbeitsverzeichnis
  beim optionalen Teststart korrigiert; Testfehler getrennt von erfolgreicher
  Basisinstallation gemeldet. Auch Betriebs-CLI verwendet das Installationsverzeichnis.
- Neue Benutzerseiten, Navigation, Dokumentation und Funktionsnachweise ergänzt.
- Zentrale Version und aktuelle Dokumentationsangaben auf 0.1.2 gesetzt.

### Betrieb und Migration

- Vor dem Update Sicherung erstellen; das Update-Skript übernimmt dies vor
  Paketinstallation und Migration. Details unter `doku/SETUP.md`.
- Explizite Migration von `0001_core_settings` auf `0002_core_users` ergänzt
  Benutzer, Sitzungen und Loginversuchszähler; vorhandene Einstellungen bleiben erhalten.
- Nach Update eines Grundsystems ohne Administrator `neofab2 create-admin`
  ausführen. Keine automatischen Standardkonten oder Benutzerimporte.
- Für das isolierte HTTP-Testnetz `SESSION_COOKIE_SECURE = false` bewusst
  konfigurieren; bei HTTPS bleibt `true` gesetzt. Danach Dienst neu starten.
- Selbstregistrierung, E-Mail-Aktivierung/-Reset, Benutzerlöschung, Plugin-Vertrag
  und Benutzerimport bleiben offen. Keine vollständige Core-Abnahme.

### Prüfungen

- Implementierungsstand: 47 Tests unter Windows/Python 3.12 bestanden,
  einschließlich Rechte, CSRF, Sitzungswiderruf, Parallelität, CLI und Migration.
- Bash-Syntax und ShellCheck für fünf Shell-Dateien bestanden.
- Implementierungsstand als Wheel/sdist gebaut und installiertes Wheel mit
  Migration, Login, Profil und Benutzerübersicht geprüft.
- Versionsänderung: Paket 0.1.2 gebaut; zentrale Version, Paketmetadaten, CLI
  und Versionsanzeige geprüft. Keine erneute vollständige Testsuite für die
  reine Versions-/Dokumentationsänderung.
- Grundsystem laut Nutzerrückmeldung im Container lauffähig; eigener LXC-/systemd-
  Test des Benutzer-Schritts, visuelle Browserprüfung und Linux-CI weiterhin offen.

### Commit für GitHub Desktop

Commit-Titel:

```text
0.1.2: Benutzerzugang, Rollen und Admin-Wiederherstellung ergänzen
```

Commit-Beschreibung:

```text
Anmeldung, CSRF-Schutz, widerrufbare Sitzungen und Anmeldebegrenzung ergänzen.
Benutzerverwaltung, Rollen, Profil und Passwortwechsel implementieren.
Erstadministrator und lokalen Notfall-Passwort-Reset bereitstellen.
Migration 0002_core_users mit Erhalt vorhandener Einstellungen hinzufügen.
Installer-Teststart korrigieren und HTTPS-/HTTP-Testkonfiguration ergänzen.
Version 0.1.2, deutsche Betriebsdokumentation und Funktionsnachweise aktualisieren.
47 Implementierungstests sowie Shell- und Paketprüfungen bestanden.
Echter LXC-Test des Benutzer-Schritts und vollständige Core-Abnahme noch offen.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.1 – 2026-09-17

Bereich: Core-Grundsystem / Installation und Betrieb.

### Änderungen

- Startfähige Flask-Application-Factory, validierte TOML-Konfiguration und
  zentrale Version für Python-Paket, CLI und Oberfläche.
- Gemeinsame Startseite mit Logo, responsivem CSS und Betriebsanzeige.
- SQLite für die erste Testinstallation, explizite Alembic-Revision
  `0001_core_settings`; keine Schemaänderung bei Anwendungsstart/Seitenaufruf.
- CLI für Konfiguration, Migration, Bereitschaftsprüfung und konsistentes Backup.
- Debian-13-Installer, Gunicorn-/systemd-Einrichtung und Fast-Forward-Update
  mit Sicherungen und kontrolliertem Abbruch.
- Automatisierte Tests, Wheel-/sdist-Paketierung und vorbereitete Linux-CI.
- Deutsche Installation, Fehlerhilfe, Betrieb und Wiederherstellung dokumentiert.

### Betrieb und Migration

Neue Testinstallation gemäß `doku/SETUP.md`. Die frühere v0.1.0 enthält kein
Laufzeitschema; die neue Datenbank entsteht ausdrücklich durch `neofab2 migrate`.
Installer verwenden ausschließlich eigene NeoFab2-Pfade und Dienstnamen.
SQLite ist zunächst Testbasis, produktive Datenbankentscheidung bleibt offen.
Keine Benutzer-/Bestandsdatenmigration; kein Eingriff in altes NeoFab.
Anmeldung, Admin-Erstzugang, Passwort-Reset, Plugin-Vertrag und Benutzerimport
folgen; keine vollständige Core-Abnahme.

### Prüfungen

- 19 lokale Tests unter Windows/Python 3.12 bestanden: Core, CLI,
  Migration, Sicherung/Restore und simulierte Update-Erfolgs-/Fehlerabläufe.
- Bash-Syntax und ShellCheck für alle vier Shell-Dateien bestanden.
- Wheel und sdist gebaut; installiertes Wheel mit Migration, Templates,
  CSS und Logo geprüft.
- Git-Diff und lokale Dokumentationslinks geprüft.
- Keine echte Debian-/LXC-/systemd-Abnahme, keine ausgeführte GitHub-CI.
- Kein Browser verbunden; visuelle Browserprüfung noch offen.

### Commit für GitHub Desktop

Commit-Titel:

```text
0.1.1: Core-Grundsystem und Debian-Installationsskripte umsetzen
```

Commit-Beschreibung:

```text
Flask-Factory, TOML-Konfiguration und explizite Alembic-Migration ergänzen.
Startseite mit Logo/Version sowie Health-Endpunkte und Betriebs-CLI erstellen.
Neue Debian-13-Installation, systemd-Service und abgesichertes Update vorbereiten.
SQLite-Backup und Wiederherstellung, Paketierung und Tests ergänzen.
19 lokale Tests, ShellCheck, Bash-Syntax und Wheel-Smoke-Test bestanden.
Deutsche Betriebsanleitungen und Funktionsnachweis aktualisieren.
Echte LXC-/systemd-Abnahme und vollständiger Core-Ausbau stehen noch aus.
```

Der Commit wird manuell in GitHub Desktop erstellt.

## Version 0.1.0 – 2026-09-17

Bereich: Projektgerüst / Distribution / Branding.

### Änderungen

- Ordnerstruktur für Core, Dienste, Plugin-API, spätere Plugins, Templates,
  statische Dateien, Migrationen und Tests vorbereitet.
- Planungsunterlagen von `docu/` nach `doku/` verschoben.
- Dauerhafte Arbeitsregeln in `AGENTS.md` festgehalten.
- Zentrale Anfangsversion in `src/neofab2/version.py` angelegt.
- Neues NeoFab2-Logo erstellt und in der README eingebunden.
- Architektur, Installationsstand und nächste Arbeitspakete dokumentiert.

### Betrieb und Migration

Keine Migration erforderlich. Noch keine startfähige Anwendung, keine
Installationsskripte und keine Core-Abnahme. Das alte NeoFab bleibt unverändert.

### Prüfungen

- Logo visuell auf Schriftzug, Motiv und Lesbarkeit geprüft.
- Verzeichnisstruktur, Dokumentationslinks und Versionsangabe geprüft.
- `git diff --check`: bestanden.
- Keine Anwendungstests: Laufzeit und Application Factory noch nicht eingerichtet.
  Der lokale Aufruf `python --version` scheiterte an einem Windows-Anmeldesitzungsfehler.

### Commit für GitHub Desktop

Commit-Titel:

```text
0.1.0: NeoFab2-Projektstruktur und neues Logo anlegen
```

Commit-Beschreibung:

```text
Grundstruktur für Core, Dienste, Plugin-API, Migrationen und Tests vorbereiten.
Projektunterlagen unter doku bündeln und dauerhafte Arbeitsregeln festhalten.
Zentrale Version 0.1.0 sowie neues NeoFab2-Logo mit README-Einbindung ergänzen.
Architektur, Installationsstand und Funktionsnachweis dokumentieren.
Struktur, Links, Versionsangabe und Logo geprüft; git diff --check bestanden.
Noch keine startfähige Anwendung oder Datenmigration.
```

Der Commit wird manuell in GitHub Desktop erstellt.
