# NeoFab2 – Versionshistorie

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
