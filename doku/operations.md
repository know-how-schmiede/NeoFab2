# Betrieb und Wiederherstellung – v0.1.15

Neu in 0.1.15: [Audit-Protokoll und Betriebsstatus](Core_Audit_und_Betriebsstatus.md).
Das normale Update führt die explizite Migration `0011_audit_status` aus.
Anschließend als Administrator unter **Administration** beide neuen Seiten prüfen.
Neue Ereignisse werden ab diesem Update erfasst; kein rückwirkendes Protokoll.
Der Versandworker meldet seinen letzten beobachteten Lauf. Standardmäßig keine
Audit-Löschung; `audit-prune --days 180` zeigt nur eine lokale Vorschau.
Die Detailanleitung beschreibt Rechte, Bereinigung, Fehlerhilfe und Prüfgrenzen.

Seit 0.1.13 gehören die Kontoverfahren und ihre Tokenmetadaten zur Sicherung.
Nach Restore öffentliche Registrierung und Passwort-Rücksetzung zunächst
deaktivieren: ein altes Backup kann zuvor verbrauchte Codes oder Sitzungen
wiederherstellen. Vor erneuter Freigabe offene Codes widerrufen, bei
sicherheitsbedingter Wiederherstellung gegebenenfalls `SECRET_KEY` wechseln.
Dieser Wechsel macht bestehende Sitzungen und Kontocodes unbrauchbar.
[Verfahren und Betriebsgrenzen](Core_Registrierung_und_Reset.md).

Ab 0.1.7 sind die App und CLI standardmäßig englisch. Deutsche Bezeichnungen
in dieser Anleitung gelten bei gewählter deutscher Kontosprache.
[Sprachwahl und Migration 0006](Core_Sprachen.md).

Plugin-Auswahl wird im Backend unter **Plugins** gespeichert und ab dem nächsten
Prozessstart übernommen. Den erforderlichen Container-Neustart führt der
Proxmox-Admin manuell aus. Die Datenbanksicherung enthält auch den Zielzustand.
[Prüfablauf und lokaler Wiederherstellungsbefehl](plugin-development.md).

Als **root im NeoFab2-Container** ausführen. Diese Fassung speichert nur die
SQLite-Core-Datenbank. Mit späteren Dateidiensten muss der Sicherungsumfang
erweitert werden. Die kleinen Testdateien seit 0.1.10 liegen als BLOB ebenfalls
in SQLite. Die Datenbank enthält Benutzer, Passwort-Hashes, Sitzungen und
seit 0.1.12 Versandaufträge samt Empfängern und Nachrichtentexten. Sicherungen entsprechend geschützt
aufbewahren. Lokaler Admin-Reset: [Core-Zugang](Core_Zugang.md).

**Versandworker seit 0.1.12:** `mail-worker --limit 20` ist ein einmaliger
CLI-Aufruf. Seit 0.1.14 richtet `setupNeoFabService` den Timer
`neofab2-mail.timer` mit `neofab2-mail.service` ein. Vor Restore als root zuerst
`systemctl stop neofab2-mail.timer` und danach
`systemctl stop neofab2-mail.service` ausführen. Das Update-Skript ab 0.1.14
stoppt diese Units vor Sicherung/Migration und startet den Timer nach erfolgreicher
Bereitschaft. Versandunits werden mitgesichert. Bei Rückkehr zu älterem Code den
Timer gestoppt lassen und mit `systemctl disable neofab2-mail.timer` deaktivieren.
Zusätzliche Worker und eigene Aufrufpläne ebenfalls stoppen; `neofab2.service` steuert
nur den Webprozess. Nach Restore zuerst SMTP in der Webverwaltung pausieren
und wartende/ungeklärte Jobs mit bereits erfolgten Zustellungen abgleichen,
bevor ein Worker startet. Ältere Sicherungen können bereits zugestellte Jobs
wieder als wartend enthalten. [Befehle, Fehlerhilfe und Grenzen](Core_SMTP_und_Versand.md).

## Dienststeuerung

```bash
systemctl stop neofab2.service
systemctl start neofab2.service
systemctl restart neofab2.service
systemctl status neofab2.service --no-pager
journalctl -u neofab2.service -n 80 --no-pager
```

`ExecStartPre` prüft das Schema, führt aber keine Migration aus.

## Zusätzliche manuelle Datenbanksicherung

### Sensible Dateien im Git-Arbeitsverzeichnis

Prüfung am 19.09.2026, unverändert Version 0.1.12 (X05/X07, Geheimnisschutz S05):
In den versionierten Dateien wurden keine echten Betriebszugangsdaten oder
Datenbank-Dumps gefunden. Die lokale Git-Historie umfasst 17 Commits;
433 Dateiinhalte aus allen lokal erreichbaren Referenzen wurden auf typische
Token-, private Schlüssel-, Passwort-Hash- und Zugangsdaten-URL-Muster geprüft,
ohne Treffer. Historische Dateinamen enthielten keine Datenbank-/Dumpdateien
oder echte `config.toml`-/`.env`-Dateien. Das ist eine gezielte Prüfung, kein
Beweis, dass beliebige Geheimnisformate ausgeschlossen sind, und keine Prüfung
entfernter, lokal nicht vorhandener Git-Referenzen.

Lokal vorhanden waren 2066 Datenbank-/Dumpdateien und 91 Konfigurationsdateien,
sämtlich bereits von Git ignoriert; insbesondere synthetische Testartefakte
unter `.test-artifacts/`. Tests enthalten bewusst synthetische Passwörter und
Testschlüssel. Diese Testquellen bleiben versioniert, erzeugte Daten nicht.

`.gitignore` schützt zusätzlich lokale TOML-Konfigurationen, `.env.*`,
Datenbankkopien samt Begleitdateien, SQL-/Dump-Backups, private Schlüssel sowie
die lokalen Verzeichnisse `data/`, `uploads/`, `logs/`, `dumps/`, `private/`
und `secrets/`. `instance/`, `.test-artifacts/` und `backups/` waren bereits
ausgeschlossen. Konfigurationsvorlagen `.env.example`, `.env.sample` und
`.env.template` sind erlaubt, dürfen aber ausschließlich Platzhalter enthalten.
Sensible Dateien mit beliebigen anderen Namen in ein ausgeschlossenes
Verzeichnis oder außerhalb des Repositorys legen. Reguläre Plugin-Ressourcen
und Python-Migrationen bleiben versionierbar.

Als **Entwicklungsbenutzer im Repository** vor einem manuellen Commit prüfen:

```bash
git status --short
git ls-files -ci --exclude-standard
git check-ignore -v --no-index config.toml .env.production backup.sql
```

Erwartet: Der zweite Befehl zeigt keine bereits versionierten ignorierten Dateien;
der dritte zeigt die passenden Ignore-Regeln auch für noch nicht angelegte Pfade.
27 sensible Beispielpfade und neun erlaubte Quell-/Vorlagenpfade wurden geprüft.
Keine bestehenden versionierten Dateien mussten aus dem Git-Index entfernt werden.
Ignore-Regeln entfernen keine bereits eingecheckten Dateien oder alten Commits.
Sollten später echte Zugangsdaten in Git entdeckt werden, reicht `.gitignore`
allein nicht: Zugangsdaten ersetzen und den betroffenen Git-Stand gesondert bereinigen.

### Sicherung außerhalb des Repositorys erstellen

```bash
install -d -m 0700 /var/backups/neofab2
NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 backup --output "/var/backups/neofab2/manual-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
```

Die SQLite-Backup-API liefert einen konsistenten Snapshot; anschließend läuft
`PRAGMA integrity_check`. Vorhandene Zieldateien werden nicht überschrieben.
Für eine vollständige Wiederherstellung auch Konfiguration und passenden
Code-/Abhängigkeitsstand sichern; das Update-Skript übernimmt diesen Umfang.
Backups zusätzlich außerhalb des Containers aufbewahren. Keine automatische
Backup-Löschung.

## Updatefehler

Fehler vor Dienststopp greifen nicht in den Dienst ein. Fehler nach Dienststopp
halten ihn an, auch wenn erst die HTTP-Prüfung nach einem Neustart fehlschlägt.
Keine automatische Rückmigration: teilweise migrierte Daten nicht mit altem
Code mischen. Zunächst Logs und ausgegebenen Sicherungspfad prüfen.

## Vollständigen Stand vor einem Update wiederherstellen

Nur eine vollständig erstellte Sicherung verwenden. Nach Fehlern während der
Sicherung kann das Verzeichnis unvollständig sein. Die Wiederherstellung setzt
auf den alten Stand zurück; spätere Änderungen werden nicht übernommen.
Die bisherigen Verzeichnisse bleiben zur Diagnose separat erhalten.

Im folgenden Block **zuerst den Beispielpfad BACKUP ersetzen**. Der Block
läuft in einer Subshell und bricht bei Fehlern ab. Nur auf demselben Container
mit unverändertem Python verwenden; die gesicherte venv braucht ihren alten Pfad.

```bash
(
set -euo pipefail
BACKUP=/var/backups/neofab2/20260917T120000Z-XXXXXX
test -s "$BACKUP/neofab2.sqlite3"
test -s "$BACKUP/config/config.toml"
test -s "$BACKUP/config/port"
test -s "$BACKUP/neofab2.service"
test -s "$BACKUP/revision.txt"
tar -tzf "$BACKUP/source.tar.gz" >/dev/null
tar -tzf "$BACKUP/venv.tar.gz" >/dev/null
systemctl stop neofab2.service

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
FAILED_APP="/opt/neofab2.failed-$STAMP"
FAILED_DATA="/var/lib/neofab2.failed-$STAMP"
FAILED_CONFIG="/etc/neofab2.failed-$STAMP"
test ! -e "$FAILED_APP"
test ! -e "$FAILED_DATA"
test ! -e "$FAILED_CONFIG"
mv /opt/neofab2 "$FAILED_APP"
mv /var/lib/neofab2 "$FAILED_DATA"
mv /etc/neofab2 "$FAILED_CONFIG"
install -d -o neofab2 -g neofab2 -m 0750 /opt/neofab2 /var/lib/neofab2

tar -xzf "$BACKUP/source.tar.gz" -C /opt/neofab2
tar -xzf "$BACKUP/venv.tar.gz" -C /opt/neofab2
cp -a "$FAILED_APP/.git" /opt/neofab2/.git
chown -R neofab2:neofab2 /opt/neofab2
runuser -u neofab2 -- git -C /opt/neofab2 checkout --detach --force "$(cat "$BACKUP/revision.txt")"
install -o neofab2 -g neofab2 -m 0640 "$BACKUP/neofab2.sqlite3" /var/lib/neofab2/neofab2.sqlite3
cp -a "$BACKUP/config" /etc/neofab2
cp -a "$BACKUP/neofab2.service" /etc/systemd/system/neofab2.service

runuser -u neofab2 -- env NEOFAB2_CONFIG=/etc/neofab2/config.toml /opt/neofab2/.venv/bin/neofab2 check
systemctl daemon-reload
systemctl start neofab2.service
systemctl status neofab2.service --no-pager
curl --fail "http://127.0.0.1:$(cat /etc/neofab2/port)/health/ready"
)
```

Erwartet: Schema bereit, Dienst aktiv und HTTP 200 mit Status `ok`. Der Checkout
steht danach bewusst abgekoppelt auf dem alten Commit. Vor dem nächsten Update
Branch und Fehlerkorrektur manuell abstimmen. Ein Betriebssystem-/Python-Wechsel
benötigt eine neue Installation statt Wiederverwendung des venv-Archivs.

SQLite-Sicherung und Wiederherstellung sind mit synthetischen Daten geprüft.
Die vollständige Betriebssystem-/Service-Wiederherstellung dieser Anleitung
muss noch in einem isolierten Debian-LXC erprobt werden.


## Benutzerimport ab 0.1.18

Explizite Migration `0012_user_import` ergänzt die stabile Zuordnung zur
Altinstallation. Vorschau schreibt nichts; Import ausschließlich nach erneuter
Prüfung und Bestätigung, mit Atomarität und Audit. Beim Backup/Restore müssen
Konten und `core_user_imports` zusammen erhalten bleiben. Quelle ist eine
abgeschlossene SQLite-Kopie; keine direkte Produktivquelle verwenden.
[Komplette Anleitung, Format, Konflikte und Rückfall](Core_Benutzerimport.md).
