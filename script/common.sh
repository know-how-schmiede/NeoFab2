#!/usr/bin/env bash
# Gemeinsame Betriebsfunktionen; nur aus den vier Einstiegsskripten laden.
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
console_section() {
  printf '\n------------------------------------------------------------\n'
  printf '%s\n' "$1"
  printf '%s\n' '------------------------------------------------------------'
}

print_access_urls() {
  local addresses address host found=0
  addresses=$(hostname -I 2>/dev/null) || addresses=''
  for address in $addresses; do
    [[ $address =~ ^[0-9a-fA-F:.]+$ ]] || continue
    host=$address
    [[ $address != *:* ]] || host="[$address]"
    printf '  http://%s:%s/login\n' "$host" "$PORT"
    found=1
  done
  [[ $found == 1 ]] || printf '  IP nicht ermittelt. Adressen im Container mit "ip -brief address" pruefen.\n'
}

wait_ready() {
  local attempt
  for attempt in {1..30}; do
    if systemctl is-active --quiet "$SERVICE" && curl --fail --silent --max-time 2 "http://127.0.0.1:$PORT/health/ready" >/dev/null; then
      console_section 'NEOFAB2 BEREIT – interne Zugriffsadressen'
      print_access_urls
      return 0
    fi
    sleep 1
  done
  printf 'Startprüfung fehlgeschlagen. Diagnose: journalctl -u %s -n 80 --no-pager\n' "$SERVICE" >&2
  return 1
}

start_summary() {
  SUMMARY_ACTION=$1
  SUMMARY_RESULT='Abgebrochen oder noch nicht abgeschlossen.'
  SUMMARY_NOTE=''
  SUMMARY_BACKUP_COMPLETE=0
  trap 'finish_summary "$?"' EXIT
}

print_summary() {
  local status=$1 service_state
  printf '\n============================================================\n'
  printf ' NEOFAB2 – ZUSAMMENFASSUNG: %s\n' "$SUMMARY_ACTION"
  printf '============================================================\n'
  if [[ $status -ne 0 ]]; then
    printf 'ERGEBNIS: FEHLER / ABBRUCH (Exit-Code %s)\n' "$status"
  else
    printf 'ERGEBNIS: %s\n' "$SUMMARY_RESULT"
  fi
  [[ -z ${SUMMARY_NOTE:-} ]] || printf 'HINWEIS: %s\n' "$SUMMARY_NOTE"
  printf '\nInstallation: %s\nDaten:        %s\nKonfiguration: %s\nDienstkonto: %s\n' "$APP_DIR" "$DATA_DIR" "$CONFIG_FILE" "$APP_USER"
  service_state=$(systemctl is-active "$SERVICE" 2>/dev/null) || service_state=${service_state:-unbekannt}
  printf 'Service: %s (%s)\n' "$SERVICE" "$service_state"
  if [[ -z ${PORT:-} && -r $CONFIG_DIR/port ]]; then PORT=$(cat "$CONFIG_DIR/port"); fi
  if [[ ${PORT:-} =~ ^[1-9][0-9]{3,4}$ ]] && ((PORT >= 1024 && PORT <= 65535)); then
    printf '\nInterne HTTP-Adressen (Erreichbarkeit von außen nicht geprüft):\n'
    print_access_urls
    printf '  Lokale Bereitschaft: http://127.0.0.1:%s/health/ready\n' "$PORT"
    printf 'HTTPS-Adresse: ggf. die konfigurierte Reverse-Proxy-Adresse verwenden.\n'
  else
    printf '\nZugriffsadresse: Port noch nicht verfügbar.\n'
  fi
  printf '\nVersion und Admin-Zugänge (keine Passwörter):\n'
  if [[ $EUID -eq 0 && -x $APP_DIR/.venv/bin/neofab2 && -f $CONFIG_FILE ]]; then
    app_cli maintenance-info 2>/dev/null || printf '  Detailinformationen nicht verfügbar; Konfiguration/Installation prüfen.\n'
  else
    printf '  Noch nicht verfügbar; Installation oder Zugriffsrechte prüfen.\n'
  fi
  if [[ -n ${BACKUP:-} ]]; then
    if [[ $SUMMARY_BACKUP_COMPLETE == 1 ]]; then
      printf '\nSicherung erstellt: %s\n' "$BACKUP"
    else
      printf '\nSicherungspfad (möglicherweise unvollständig): %s\n' "$BACKUP"
    fi
    printf 'Wiederherstellung: %s/doku/operations.md\n' "$APP_DIR"
  fi
  printf '\nWICHTIGE BEFEHLE – als root im NeoFab2-Container:\n'
  printf '  bash %q/script/setupNeoFabService\n' "$APP_DIR"
  printf '  bash %q/script/upDateNeoFabService\n' "$APP_DIR"
  printf '  bash %q/script/resetAdminPassword\n' "$APP_DIR"
  printf '  systemctl status %q --no-pager\n' "$SERVICE"
  printf '  systemctl restart %q\n' "$SERVICE"
  printf '  journalctl -u %q -n 80 --no-pager\n' "$SERVICE"
  printf '  runuser -u %q -- env NEOFAB2_CONFIG=%q %q check\n' "$APP_USER" "$CONFIG_FILE" "$APP_DIR/.venv/bin/neofab2"
  printf '============================================================\n'
}

finish_summary() {
  local status=$1
  trap - EXIT ERR
  # Die Diagnose darf weder den Exit-Code ändern noch den Fehler-Handler erneut
  # auslösen; kein Start/Stop, keine Migration und keine Geheimnisse ausgeben.
  (set +e; print_summary "$status") || true
  exit "$status"
}

# Eigene Units; keine Änderung am alten NeoFab-Dienst.
MAIL_SERVICE=neofab2-mail.service
MAIL_TIMER=neofab2-mail.timer
MAIL_UNIT=/etc/systemd/system/$MAIL_SERVICE
MAIL_TIMER_UNIT=/etc/systemd/system/$MAIL_TIMER

stop_mail_worker() {
  if [[ -f $MAIL_TIMER_UNIT ]]; then systemctl stop "$MAIL_TIMER"; fi
  if [[ -f $MAIL_UNIT ]]; then systemctl stop "$MAIL_SERVICE"; fi
}

install_mail_worker() {
  # Vorhandene lokale Anpassungen erhalten, aber Pfad und Benutzer prüfen.
  if [[ -e $MAIL_UNIT ]]; then
    grep -Fxq "WorkingDirectory=$APP_DIR" "$MAIL_UNIT" || { printf 'FEHLER: Versanddienst-Pfad passt nicht.\n' >&2; return 1; }
    grep -Fxq "User=$APP_USER" "$MAIL_UNIT" || { printf 'FEHLER: Versanddienst-Benutzer passt nicht.\n' >&2; return 1; }
  else
    cat > "$MAIL_UNIT" <<EOF
[Unit]
Description=NeoFab2 mail queue
After=network.target

[Service]
Type=oneshot
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=NEOFAB2_CONFIG=$CONFIG_FILE
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$APP_DIR/.venv/bin/neofab2 mail-worker --limit 20
TimeoutStartSec=240
TimeoutStopSec=30
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR
EOF
    chmod 0644 "$MAIL_UNIT"
  fi
  if [[ ! -e $MAIL_TIMER_UNIT ]]; then
    cat > "$MAIL_TIMER_UNIT" <<EOF
[Unit]
Description=NeoFab2 mail queue schedule

[Timer]
OnActiveSec=15s
OnUnitInactiveSec=30s
AccuracySec=1s
Unit=$MAIL_SERVICE

[Install]
WantedBy=timers.target
EOF
    chmod 0644 "$MAIL_TIMER_UNIT"
  fi
  systemd-analyze verify "$MAIL_UNIT" "$MAIL_TIMER_UNIT"
  systemctl daemon-reload
  systemctl enable --now "$MAIL_TIMER"
  systemctl is-active --quiet "$MAIL_TIMER"
}
