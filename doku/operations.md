# Betrieb und Wiederherstellung – v0.1.1

Als **root im NeoFab2-Container** ausführen. Diese Fassung speichert nur die
SQLite-Core-Datenbank. Mit späteren Dateidiensten muss der Sicherungsumfang
erweitert werden; es gibt noch keine Uploads oder Benutzer.

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
