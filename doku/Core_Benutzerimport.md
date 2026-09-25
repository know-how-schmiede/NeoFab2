# Benutzerimport – Vertrag für 0.1.18

## Korrektur 0.1.21: Import nach Vorschau abschließen

Bei gemischten Ergebnissen wurde bislang die gesamte Bestätigung ausgeblendet.
Nun können Administratoren die als „Neu anlegen“ oder „Aktualisieren“ markierten
Konten importieren, auch wenn andere Zeilen Konflikte enthalten:

1. Vorschau prüfen, insbesondere Anzahl und Gründe der Konflikte.
2. „Konflikte überspringen und nur die bereiten Konten importieren“ ausdrücklich
   ankreuzen. Bestehende Konfliktkonten werden weder überschrieben noch verknüpft.
3. Dieselbe Datei erneut auswählen, Importbestätigung ankreuzen und Import ausführen.
4. Ergebnisbericht prüfen: Konflikte bleiben sichtbar und wurden nicht importiert.

Bei ausschließlich Konflikten oder unveränderten Konten erklärt die Seite, dass
keine Konten zum Import bereit sind. Datei gegebenenfalls korrigieren und neu prüfen.
Der Schutz des letzten aktiven Administrators blockiert weiterhin den gesamten
Import. Veraltete Vorschauen, fehlende Bestätigung und Datenbankfehler führen zu
keinen Änderungen. Löschmarkierungen werden nicht umgangen.
Die CLI bleibt unverändert strikt: Konflikte verhindern dort die Übernahme.

Keine neue Migration; Schema bleibt `0013_user_deletion`. Normalen
[Updateablauf](../script/README.md) verwenden. Ergebnisprüfung als **root**, mit
Standardpfaden und Ausführung durch **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: **0.1.21**, Schema bereit. Bei alter Oberfläche Installation und
Versionsanzeige prüfen. Keine produktive Importausführung durch Codex.

Seit Schema `0013_user_deletion` darf `core_user_imports.user_id` leer sein: Nach bestätigter Kontolöschung bleibt die Quellzuordnung als Sperrmarkierung erhalten. Wiederimport derselben Quelle/Quell-ID liefert `target_deleted` und legt das Konto nicht erneut an. [Löschung und Wiederherstellung](Core_Benutzerloeschung.md).

Ergänzung vom 25.09.2026, aktuelle Version auf Benutzerwunsch **0.1.9**:
[NeoFab2-Benutzerexport](Core_Benutzerexport.md) liefert natives Format 2, das
dieser Import zusätzlich akzeptiert. Format 1 und seine Altrollen bleiben gültig.
Format 2 verwendet `staff` statt `worker` und verlangt `activation_pending` als
Boolean. Die folgenden Format-1-Regeln beziehen sich auf den Altimport.

Paket 6: U09/N04/U06, ergänzend U01/U05/U07/S09/X07.
Importdienst, Admin-Oberfläche, CLI und explizite Migration sind implementiert.
Automatisierte Nachweise stehen in `tests/core/test_user_import.py`.
Kein Produktivimport, keine Änderung an NeoFab und keine Core-Abnahme.

## Festgelegte Regeln vor Umsetzung

- Quelle ist ein geschützter JSON-Export mit Formatversion 1, stabiler
  Installationskennung und numerischen Alt-IDs. Der bisherige NeoFab-Webexport
  ohne IDs und Theme ist kein geeignetes Importformat und wird abgewiesen.
  Ein neues lokales Werkzeug liest dafür ausschließlich eine SQLite-Kopie.
- Rollen: `user` → `user`, `worker` → `staff`, `admin` → `admin`.
  Andere Rollen blockieren den gesamten Import; keine automatische Aufwertung.
- Neue gelöschte Altbenutzer werden übersprungen. Wenn ein bereits übernommener
  Benutzer später als gelöscht erscheint, entsteht ein Konflikt; es findet
  weder Löschung noch automatische Reaktivierung statt.
- Inaktive Konten bleiben inaktiv. Fehlende/ungültige Statuswerte sind Fehler.
  Alte Sitzungen, Aktivierungs-/Resetcodes, Aufträge, Fachrechte und fachliche
  Benachrichtigungspräferenzen werden nicht übernommen; kein E-Mail-Versand.
- Nur begrenzte kompatible Werkzeug-scrypt-/PBKDF2-SHA256-Hashes werden übernommen.
  Unbrauchbare Hashes ergeben gesperrte Konten mit ausstehender Aktivierung und
  zufälligem unbekanntem Passwort; der Admin muss ein neues Passwort setzen und
  die Freischaltung ausdrücklich entscheiden. Kein Passwort erscheint im Bericht.
- E-Mail-Kollisionen mit bestehenden Konten oder innerhalb der Quelle sind
  Konflikte. Keine Verknüpfung anhand der E-Mail, kein Überschreiben des Erstadmins.
- Wiederholung mit unveränderter Quelle verändert keine Konten. Geänderte
  Quelldaten aktualisieren nur eindeutig zugeordnete Konten, deren Zielstand seit
  dem letzten Import unverändert ist. Lokale Änderungen plus Quellenänderung
  blockieren den Import. Zielzustand und Quelle werden vor Bestätigung erneut
  geprüft; veraltete Vorschau wird abgewiesen.
- Profil-Auswahllisten müssen vorher passende aktive Einträge enthalten. Der
  Import legt keine Stammdaten an. Letzter aktiver Admin bleibt geschützt.
- Schreiben erfolgt atomar einschließlich Zuordnung und Audit. Ohne ausdrückliche
  Freigabe zum Überspringen blockiert jeder Konflikt. Bei bestätigtem Überspringen
  werden nur bereite Zeilen gemeinsam atomar übernommen. Vorschau schreibt nichts.

## Umsetzung und Grenzen

`prepare-user-import` liest die Tabelle `user` einer **abgeschlossenen SQLite-
Sicherungskopie** mit `mode=ro&immutable=1`. Quelle nicht gleichzeitig bearbeiten.
Keine Produktivdatenbank direkt angeben. WAL-Dateien neben der Kopie werden
abgewiesen: eine konsistente SQLite-Sicherung verwenden, keine isoliert kopierte
Hauptdatei eines laufenden WAL-Betriebs. NeoFab-Code wird nicht importiert.
Views/virtuelle Tabellen werden nicht als Benutzerquelle akzeptiert.

Benötigte Spalten: `id`, `email`, `password_hash`, `role`, `language`,
`theme_mode`, `is_active`, `deleted_at`, `created_at` und alle unten genannten
Profilfelder. Fehlende Spalten brechen den Export ab. Der alte Quellcode wurde
zur Feld-/Rollenzuordnung gelesen, keine alte Datenbank geöffnet oder verändert.
Andere Datenbanksysteme werden nicht direkt unterstützt.

Formatversion 1 (Beispiel ohne nutzbares Passwort; führt zu gesperrtem Konto):

```json
{
  "format": 1,
  "source": "neofab-test",
  "users": [{
    "id": 40,
    "email": "synthetic@example.org",
    "display_name": "Synthetic User",
    "role": "worker",
    "active": false,
    "deleted": false,
    "password_hash": "",
    "locale": "de",
    "theme": "dark",
    "created_at": 1700000000,
    "details": {
      "salutation": "", "first_name": "Synthetic", "last_name": "User",
      "address": "", "position": "", "cost_center": "",
      "study_program": "", "note": ""
    }
  }]
}
```

Alle Felder sind erforderlich; unbekannte Felder (auch Tokens), doppelte
JSON-Schlüssel und Quell-IDs werden abgewiesen. `source` ist eine feste Kennung
je Altinstallation: Kleinbuchstabe, danach Kleinbuchstaben/Ziffern/Bindestrich/
Unterstrich, insgesamt höchstens 64 Zeichen. **Bei Wiederholung nie ändern.**
Quell-IDs sind positive Ganzzahlen unter 2^63; gleiche E-Mails mit anderer
Quellkennung werden nicht automatisch verknüpft. Fehlende Zeilen löschen nichts.

Grenzen: 5000 Benutzer, 8 MiB JSON über CLI; im Browser gilt zusätzlich das
vorhandene Request-Limit von 1 MiB einschließlich Multipart-Overhead. Größere
Exporte bis 8 MiB über CLI verarbeiten. Kein Hochsetzen der Webgrenze erforderlich.
Leerer Export ist zulässig und verändert nichts. Quelldaten werden vollständig
validiert, bevor Konten geschrieben werden. Bereits gelöschte Quellkonten werden
beim Vorbereiten auf ID und neutrale Pflichtfelder reduziert.

Profil: Anrede, Vorname, Nachname, Adresse, Position, organisatorische Kostenstelle,
Studiengang und Notiz; vorhandene Core-Feldgrenzen gelten. Position/Studiengang/
Kostenstelle benötigen passende aktive Core-Auswahllisten. Vorhandene unverändert
übernommene Zuordnungen dürfen bei späteren Updates inaktive Optionen behalten.
Keine Kürzung oder automatische Stammdatenerzeugung. Anzeigename aus Vor-/Nachname,
sonst E-Mail-Lokalteil; länger als 100 Zeichen → Konflikt, gezielt korrigieren.
Sprache `en/de/fr`, Theme `system/light/dark`; unbekannte Werte blockieren.
Altzeit `created_at` ohne Zone gilt entsprechend NeoFab als UTC; Speicherung in
Epoch-Sekunden. `last_login_at` wird nicht übernommen.

Hash-Vertrag: Werkzeug `scrypt:32768:8:1` oder `pbkdf2:sha256` mit 1 bis
1.000.000 Iterationen, ASCII-alphanumerischem Salt (1–64 Zeichen) und korrekter
Hex-Länge. Algorithmus und Arbeitsaufwand sind begrenzt, um teure/manipulierte
Hashes beim Login abzuweisen. Ein formal passender Hash beweist nicht, dass das
reale Altpasswort bekannt ist: vor Freischaltung kontrollierte Konten prüfen.
Die Tests weisen Kompatibilität mit synthetischen Passwörtern nach. Ungültige
Hashes werden niemals als Login-Hash gespeichert; zufälliges unbekanntes Passwort,
`active=false` und `activation_pending=true` verhindern einen versehentlichen Login.
Die Oberfläche bezeichnet diesen Core-Status als ausstehende Aktivierung; es wird
**keine Aktivierungs-E-Mail** verschickt. Passwort und Freischaltung unter
Benutzerverwaltung ausdrücklich setzen. Bereits inaktive Altbenutzer mit gültigem
Hash bleiben gesperrt, ohne neue Aktivierungscodes.

Der Bericht zeigt Quell-ID, gegebenenfalls Ziel-ID (CLI), E-Mail, Rolle,
Aktivstatus und feste Ergebniskategorien. Er enthält keine Hashes, Passwörter,
Tokens oder Profilnotizen. Er kann personenbezogene E-Mails enthalten und ist
vertraulich zu behandeln. Fehlertexte geben ungültige Quelldaten nicht wieder.
Audit enthält `user.imported` mit numerischem Ziel und gegebenenfalls Admin-ID;
lokale CLI-Importe haben keinen Webbenutzer als Akteur. Unveränderte/übersprungene
Konten erzeugen keine neuen Kontoereignisse.

## Update auf 0.1.18

Normales Update nach [SETUP](SETUP.md) ausführen. Explizite Migration
`0012_user_import` ergänzt `core_user_imports` mit Quellkennung/Alt-ID, eindeutigem
Zielkonto und Fingerabdrücken. Bestehende Konten bleiben unverändert. Normaler
Webstart oder Vorschau legen kein Schema an. Bei fehlender Migration ist die
Bereitschaftsprüfung nicht erfolgreich.

Als **root**, Standardinstallation, Ausführung durch **neofab2**:

```bash
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 --version
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
```

Erwartet: **0.1.18**, Datenbank/Schema bereit. Bei fehlendem Schema den
kontrollierten Updateablauf einschließlich Sicherung und Migration verwenden.
Kein eigenständiger Produktivimport ist durch diese Anleitung beauftragt.

## Isolierter Importtest – lokaler Betriebsweg

Nur synthetische Quelldaten und eine isolierte NeoFab2-Testinstallation verwenden.
Beispiel-Standardpfade unten beziehen sich auf diese Testinstallation. Eine zuvor
erstellte synthetische SQLite-Sicherung liegt als
`/var/lib/neofab2/import/legacy-test.sqlite3` vor. **root** richtet den geschützten
Arbeitsordner ein; die Kopie muss für `neofab2` lesbar sein:

```bash
install -d -m 0700 -o neofab2 -g neofab2 /var/lib/neofab2/import
```

Als **root**, Ausführung durch **neofab2**:

```bash
runuser -u neofab2 -- /opt/neofab2/.venv/bin/neofab2 prepare-user-import \
  --database /var/lib/neofab2/import/legacy-test.sqlite3 \
  --source-id neofab-test \
  --output /var/lib/neofab2/import/users-test.json

runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml \
  /opt/neofab2/.venv/bin/neofab2 users-import /var/lib/neofab2/import/users-test.json
```

Erwartet: Exportdatei mit Modus **0600**, kein Überschreiben einer vorhandenen Datei.
Vorschau zeigt JSON mit `applied: false`, `counts` und `rows`; kein Konto geändert,
kein Versand. `conflict > 0` liefert CLI-Exitcode 1 und blockiert den Import.
Rollen (einschließlich übernommener Admins), Status, Anzahl und Quelle prüfen.
Den angezeigten `plan`-Wert zur Bestätigung übernehmen:

```bash
read -r -p 'Plan-Wert aus der geprüften Vorschau: ' IMPORT_PLAN
runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml \
  /opt/neofab2/.venv/bin/neofab2 users-import /var/lib/neofab2/import/users-test.json \
  --apply --expected-plan "$IMPORT_PLAN"
unset IMPORT_PLAN
```

Das `read -p`-Beispiel in **Bash** ausführen. Anschließende Rückfrage nur nach
Prüfung mit `y` bestätigen; `n` bricht unverändert ab. Der Plan-Wert ist kein
Passwort, aber an die geprüfte Quelle und den vollständigen relevanten Zielstand
gebunden. Der Import prüft ihn nach Bestätigung unter Schreibsperre erneut.
Schon eine andere Änderung an Konten oder Auswahllisten verlangt eine neue
Vorschau. Geänderter `SECRET_KEY` macht bestehende Plan-Werte unbrauchbar.

Ergebnis: `applied: true`, neue Ziel-IDs, keine Hashes. Wiederholte Vorschau mit
derselben Quelle zeigt `unchanged`; keine doppelten Konten. Für einen
aufzubewahrenden Bericht Ausgabe in eine geschützte Datei umleiten (`umask 077`)
oder aus der Konsole übernehmen; nicht in Git einchecken. Der Import speichert
keine vollständige Quellkopie oder Berichtshistorie im Websystem.

## Admin-Oberfläche

Als angemeldeter **Administrator**: Benutzerverwaltung → Benutzerimport.
Vorbereitete JSON-Datei hochladen und „Import prüfen“ wählen. Bericht kontrollieren.
Bei konfliktfreier Vorschau dieselbe Datei erneut auswählen, Bestätigungsfeld
setzen und „Import ausführen“ wählen. Die zweite Auswahl vermeidet eine Ablage
von Passwort-Hashes in Session-Cookies oder zwischengespeicherten Webformularen.
Es werden nur der signierte Plan-Wert und CSRF-Token zurückgegeben. Mitarbeiter,
Benutzer und gesperrte Konten erhalten keine Importberechtigung; direkte Aufrufe
sind ebenfalls geschützt. EN/DE/FR-Beschriftungen vorhanden.

## Fehlerhilfe und Wiederholung

- `invalid_fields`: Quellrolle, Pflichtfelder, Typen, Sprache, Theme, Name und
  Feldlängen prüfen. Keine automatische Zuordnung unbekannter Rollen.
- `email_collision` / `duplicate_email`: Kollision fachlich klären. Keine
  Zusammenführung durch Umnummerierung oder wechselnde Quellkennung erzwingen.
- `unknown_option`: passenden aktiven Eintrag in Core-Auswahllisten pflegen,
  dann Vorschau wiederholen.
- `reset_required`: Konto bleibt gesperrt. Neues Passwort und Freischaltung als
  Admin separat entscheiden; nicht durch Wiederimport zu aktivieren versuchen.
- `local_changes`: Ziel wurde seit dem Import verändert und Quelle ebenfalls.
  Beide Stände fachlich vergleichen; der Import überschreibt diese Änderung
  nicht. In dieser Version gibt es keinen „Konflikt ignorieren“-Schalter.
- `source_deleted` bei bereits verknüpftem Konto: gesonderte Entscheidung über
  Kontosperre/Datenschutz nötig, keine automatische Löschung durch Import.
- Veraltete Vorschau: erneute Vorschau erstellen und prüfen. Wiederholungen einer
  schon ausgeführten Vorschau sind nicht gültig; neue Vorschau ist idempotent.
- Datenbankfehler: Importtransaktion zurückgerollt. Datenbank/Schema und Rechte
  lokal prüfen; keine Logs oder Exporte mit Passwort-Hashes weitergeben.
- Exportfehler: nur konsistente eigenständige SQLite-Kopie mit vollständigem
  bekannten Schema verwenden; Ziel muss neu sein. Auch eine bei Schreibfehlern
  unvollständige Ausgabedatei nicht als gültigen Export verwenden.

## Sicherung, Rückfall und spätere Umstellung

Vor tatsächlicher Übernahme den dokumentierten Sicherungsablauf verwenden.
Sicherung umfasst Konten und `core_user_imports` gemeinsam. Ein Restore ohne
Zuordnung wäre kein vollständiger Restore. Bei Rückfall passenden Code und
vollständige Sicherung wiederherstellen; keine Tabellen manuell entfernen.
Nach einem Restore erneut Vorschau erzeugen. Neustart und Restore der Zuordnung
sind synthetisch geprüft.

Geänderte importierte Konten verlieren alle bestehenden Sitzungen und offenen
Kontocodes; unveränderte Konten behalten ihre lokalen Änderungen/Sitzungen.
Ein letzter Import vor Umstellung setzt einen separat vereinbarten Änderungsstopp
im Altsystem voraus. Es gibt keine laufende Synchronisierung. Nach Freischaltung
entstandene NeoFab2-Daten werden durch einen Rückfall nicht automatisch ins alte
NeoFab übertragen. Produktivimport, Freischaltung und Abschaltung bleiben eigene
Betriebsentscheidungen. P1/P2 und vollständige Core-/Browser-/LXC-Abnahme bleiben
unabhängig davon offen.

## Entwicklungsprüfung

Als **Entwicklungsbenutzer**, im Repository, mit installierter Entwicklungsumgebung:

```bash
python -m pytest -q tests/core/test_user_import.py
python -m pytest -q
python -m build
```

Die Tests erzeugen selbst ausschließlich synthetische Alt-Snapshots und Zielkonten
in temporären Verzeichnissen. Keine echte NeoFab-Datei ist dafür nötig.
Das installierte Wheel wird zusätzlich über `tests/wheel_smoke.py` einschließlich
Importvorschau, Ausführung und Wiederholung geprüft. Ergebnisse der jeweiligen
Version stehen in der [Versionshistorie](Version_Timeline.md).
