#!/usr/bin/env bash
# Gemeinsame Betriebsfunktionen; nur aus den drei Einstiegsskripten laden.
# Variablen werden von den aufrufenden Skripten verwendet.
# shellcheck disable=SC2034
set -Eeuo pipefail

APP_USER=neofab2
APP_DIR=/opt/neofab2
DATA_DIR=/var/lib/neofab2
CONFIG_DIR=/etc/neofab2
CONFIG_FILE=$CONFIG_DIR/config.toml
SERVICE=neofab2.service
UNIT=/etc/systemd/system/$SERVICE
BACKUP_ROOT=/var/backups/neofab2

die() { printf 'FEHLER: %s\n' "$*" >&2; exit 1; }
prompt() {
  local answer
  read -r -p "$2 [$3]: " answer || die 'Eingabe abgebrochen.'
  printf -v "$1" '%s' "${answer:-$3}"
}
require_root() {
  [[ $EUID -eq 0 ]] || die 'Als root im Debian-Container ausführen.'
  [[ -f /etc/os-release ]] || die 'Debian 13 erforderlich.'
  # Betriebssystemdatei, kein Inhalt aus dem Repository.
  # shellcheck source=/dev/null
  . /etc/os-release
  [[ $ID == debian && $VERSION_ID == 13 ]] || die 'Dieses Skript unterstützt Debian 13.'
  command -v flock >/dev/null || die 'flock (util-linux) fehlt.'
  exec 9>/run/lock/neofab2-maintenance.lock
  flock -n 9 || die 'Eine andere NeoFab2-Wartung läuft bereits.'
  umask 027
}
as_app() { runuser -u "$APP_USER" -- "$@"; }
app_cli() { (cd -- "$APP_DIR" && as_app env NEOFAB2_CONFIG="$CONFIG_FILE" "$APP_DIR/.venv/bin/neofab2" "$@"); }
require_install() {
  [[ -x $APP_DIR/.venv/bin/neofab2 && -f $CONFIG_FILE && -d $APP_DIR/.git ]] || die 'Zuerst setupNeoFab ausführen.'
}
read_port() {
  [[ -f $CONFIG_DIR/port ]] || die 'Port-Konfiguration fehlt.'
  PORT=$(cat "$CONFIG_DIR/port")
  validate_port
}
validate_port() {
  if [[ ! $PORT =~ ^[1-9][0-9]{3,4}$ ]]; then die 'Port muss zwischen 1024 und 65535 liegen.'; fi
  if ((PORT < 1024 || PORT > 65535)); then die 'Port muss zwischen 1024 und 65535 liegen.'; fi
}
verify_service() {
  [[ -f $UNIT ]] || die 'NeoFab2-Service fehlt; zuerst setupNeoFabService ausführen.'
  grep -Fxq "WorkingDirectory=$APP_DIR" "$UNIT" || die 'Service-Pfad passt nicht zur Installation.'
  grep -Fxq "User=$APP_USER" "$UNIT" || die 'Service-Benutzer passt nicht zur Installation.'
}
wait_ready() {
  local attempt
  for attempt in {1..30}; do
    if systemctl is-active --quiet "$SERVICE" && curl --fail --silent --max-time 2 "http://127.0.0.1:$PORT/health/ready" >/dev/null; then
      printf 'NeoFab2 bereit: http://<Container-IP>:%s\n' "$PORT"
      return 0
    fi
    sleep 1
  done
  printf 'Startprüfung fehlgeschlagen. Diagnose: journalctl -u %s -n 80 --no-pager\n' "$SERVICE" >&2
  return 1
}
