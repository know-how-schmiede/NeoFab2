# NeoFab2 – Versionshistorie

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
