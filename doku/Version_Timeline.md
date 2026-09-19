# NeoFab2 – Versionshistorie

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
