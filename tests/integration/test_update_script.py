"""X03: Update-Steuerung mit simulierten OS-Kommandos, kein systemd-Echttest."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

BASH = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe") if os.name == "nt" else shutil.which("bash")
pytestmark = pytest.mark.skipif(not BASH or not Path(BASH).is_file(), reason="Bash nicht verfügbar")


@pytest.mark.parametrize("failure", ["", "dirty", "fetch", "backup", "pip", "migrate", "ready", "mail"])
def test_update_failure_never_reports_success(tmp_path, failure):
    scripts = Path(__file__).resolve().parents[2] / "script"
    shutil.copy(scripts / "upDateNeoFabService", tmp_path)
    # All OS-affecting commands are functions; only mktemp writes under tmp_path.
    (tmp_path / "common.sh").write_text((scripts / "common.sh").read_text(encoding="utf-8") + r'''
set -Eeuo pipefail
APP_DIR="$TEST_ROOT/app"
CONFIG_FILE="$TEST_ROOT/config.toml"
CONFIG_DIR="$TEST_ROOT/config"
UNIT="$TEST_ROOT/neofab2.service"
SERVICE=neofab2.service
BACKUP_ROOT="$TEST_ROOT"
MAIL_UNIT="$TEST_ROOT/neofab2-mail.service"
MAIL_TIMER_UNIT="$TEST_ROOT/neofab2-mail.timer"
install_mail_worker() { echo mail-install >> "$TEST_ROOT/log"; [[ $FAIL_STEP != mail ]]; }
die() { echo "FEHLER: $*"; exit 1; }
require_root() { :; }
require_install() { :; }
verify_service() { :; }
read_port() { PORT=8080; }
prompt() { printf -v "$1" '%s' j; }
app_cli() { echo "cli $*" >> "$TEST_ROOT/log"; [[ "$*" != "$FAIL_STEP" ]]; }
as_app() {
  echo "as_app $*" >> "$TEST_ROOT/log"
  case "$*" in
    *'status --porcelain') [[ $FAIL_STEP != dirty ]] || echo dirty ;;
    *'symbolic-ref'*) echo main ;;
    *'fetch origin') [[ $FAIL_STEP != fetch ]] ;;
    *'rev-parse --verify'*) echo new ;;
    *'rev-parse HEAD') echo old ;;
    *'pip install'*) [[ $FAIL_STEP != pip ]] ;;
  esac
}
systemctl() { echo "systemctl $*" >> "$TEST_ROOT/log"; }
env() { echo backup >> "$TEST_ROOT/log"; [[ $FAIL_STEP != backup ]]; }
install() { :; }
chmod() { :; }
cp() { :; }
tar() { :; }
wait_ready() { [[ $FAIL_STEP != ready ]]; }
''', encoding="utf-8")
    (tmp_path / "neofab2-mail.service").write_text("synthetic")
    (tmp_path / "neofab2-mail.timer").write_text("synthetic")
    env = {**os.environ, "TEST_ROOT": tmp_path.as_posix(), "FAIL_STEP": failure}
    result = subprocess.run([BASH, (tmp_path / "upDateNeoFabService").as_posix()], env=env, capture_output=True, text=True)
    log = (tmp_path / "log").read_text()
    if failure not in {"dirty", "fetch"}:
        assert log.index("stop neofab2-mail.timer") < log.index("stop neofab2-mail.service") < log.index("backup")
    if failure in {"backup", "pip", "migrate", "ready"}:
        assert "mail-install" not in log
    if not failure:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Update erfolgreich" in result.stdout
        assert log.index("systemctl start neofab2.service") < log.index("mail-install")
        assert log.index("backup") < log.index("merge --ff-only") < log.index("cli migrate") < log.index("systemctl start")
    else:
        assert result.returncode != 0
        assert "Update erfolgreich" not in result.stdout
        if failure in {"dirty", "fetch"}:
            assert "systemctl stop" not in log
        else:
            actions = [line for line in log.splitlines() if not line.startswith("systemctl is-active")]
            assert actions[-1] == "systemctl stop neofab2.service"
        assert "ERGEBNIS: FEHLER / ABBRUCH" in result.stdout
    assert "NEOFAB2" in result.stdout and "ZUSAMMENFASSUNG" in result.stdout
