"""X01-X04: real summary functions with simulated OS state only."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest
from click.testing import CliRunner

from neofab2.cli import main

BASH = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe") if os.name == "nt" else shutil.which("bash")
SCRIPTS = Path(__file__).resolve().parents[2] / "script"


@pytest.mark.skipif(not BASH or not Path(BASH).is_file(), reason="Bash unavailable")
@pytest.mark.parametrize("exit_code", [0, 7, 130])
def test_summary_keeps_exit_code_handles_missing_metadata_and_formats_ipv6(tmp_path, exit_code):
    script = tmp_path / "summary.sh"
    script.write_text((SCRIPTS / "common.sh").read_text(encoding="utf-8") + r'''
APP_DIR="$TEST_ROOT/missing installation"
CONFIG_FILE="$TEST_ROOT/missing.toml"
PORT=8080
systemctl() { printf 'inactive\n'; return 3; }
hostname() { printf '192.0.2.10 2001:db8::10\n'; }
start_summary 'Synthetic operation'
SUMMARY_RESULT='Synthetic completion'
exit "$TEST_EXIT"
''', encoding="utf-8", newline="\n")
    result = subprocess.run([BASH, script.as_posix()], capture_output=True, text=True, encoding="utf-8",
                            env={**os.environ, "TEST_ROOT": tmp_path.as_posix(), "TEST_EXIT": str(exit_code)})
    assert result.returncode == exit_code, result.stderr
    assert "ZUSAMMENFASSUNG: Synthetic operation" in result.stdout
    assert "http://192.0.2.10:8080/login" in result.stdout
    assert "http://[2001:db8::10]:8080/login" in result.stdout
    assert "(inactive)" in result.stdout
    assert "resetAdminPassword" in result.stdout and "journalctl" in result.stdout
    assert "keine Passwörter" in result.stdout
    assert ("FEHLER / ABBRUCH" in result.stdout) == (exit_code != 0)
    assert "<Container-IP>" not in result.stdout


@pytest.mark.skipif(not BASH or not Path(BASH).is_file(), reason="Bash unavailable")
def test_ready_output_has_separators_and_detected_addresses(tmp_path):
    script = tmp_path / "ready.sh"
    script.write_text((SCRIPTS / "common.sh").read_text(encoding="utf-8") + r'''
PORT=8080
hostname() { printf '192.0.2.10 2001:db8::10\n'; }
systemctl() { :; }
curl() { :; }
wait_ready
hostname() { return 1; }
print_access_urls
''', encoding="utf-8", newline="\n")
    result = subprocess.run([BASH, script.as_posix()], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("------------------------------------------------------------") == 2
    assert "http://192.0.2.10:8080/login" in result.stdout
    assert "http://[2001:db8::10]:8080/login" in result.stdout
    assert "IP nicht ermittelt" in result.stdout
    assert "<Container-IP>" not in result.stdout


@pytest.mark.skipif(not BASH or not Path(BASH).is_file(), reason="Bash unavailable")
@pytest.mark.parametrize("script_name", ["setupNeoFab", "resetAdminPassword", "setupNeoFabService"])
def test_entrypoints_summarize_cancel_failure_or_success_without_real_services(tmp_path, script_name):
    shutil.copy(SCRIPTS / script_name, tmp_path)
    # Existing fake unit skips unit creation and avoids touching /etc.
    (tmp_path / "unit").write_text("synthetic", encoding="utf-8")
    overrides = r'''
APP_DIR="$TEST_ROOT"
CONFIG_FILE="$TEST_ROOT/missing.toml"
UNIT="$TEST_ROOT/unit"
MAIL_UNIT="$TEST_ROOT/neofab2-mail.service"
MAIL_TIMER_UNIT="$TEST_ROOT/neofab2-mail.timer"
require_root() { :; }
require_install() { :; }
read_port() { PORT=8080; }
verify_service() { :; }
prompt() { printf -v "$1" '%s' n; }
hostname() { return 1; }
systemctl() { printf 'active\n'; }
systemd-analyze() { :; }
app_cli() { :; }
wait_ready() { :; }
'''
    # The service script checks systemd's presence. Bypass only this OS guard
    # in the isolated harness; its actual service operations are still mocked.
    p = tmp_path / script_name
    s = p.read_text(encoding="utf-8")
    if script_name == "setupNeoFabService":
        s = s.replace("[[ -d /run/systemd/system ]] || die 'systemd läuft nicht. Im Debian-Container ausführen.'", ": # simulated systemd host")
    p.write_text(s, encoding="utf-8", newline="\n")
    (tmp_path / "common.sh").write_text((SCRIPTS / "common.sh").read_text(encoding="utf-8") + overrides, encoding="utf-8", newline="\n")
    result = subprocess.run([BASH, p.as_posix()], capture_output=True, text=True, encoding="utf-8",
                            env={**os.environ, "TEST_ROOT": tmp_path.as_posix()})
    assert result.returncode == 0, result.stderr
    assert "ZUSAMMENFASSUNG" in result.stdout
    if script_name == "setupNeoFab":
        assert "ERGEBNIS: Abgebrochen" in result.stdout
        assert "Basisinstallation erfolgreich" not in result.stdout
    elif script_name == "setupNeoFabService":
        assert "ERGEBNIS: Webdienst bereit" in result.stdout
        assert "IP nicht ermittelt" in result.stdout
    else:
        assert "ERGEBNIS: Admin-Passwort geändert" in result.stdout


def test_maintenance_info_is_read_only_and_never_prints_secrets(tmp_path, monkeypatch):
    config = tmp_path / "config.toml"
    runner = CliRunner()
    assert runner.invoke(main, ["init-config", "--output", str(config), "--data-dir", str(tmp_path)]).exit_code == 0
    monkeypatch.setenv("NEOFAB2_CONFIG", str(config))
    result = runner.invoke(main, ["maintenance-info"])
    assert result.exit_code == 0
    assert "HTTPS required" in result.output and "unavailable" in result.output
    assert not (tmp_path / "neofab2.sqlite3").exists()
    assert runner.invoke(main, ["migrate"]).exit_code == 0
    password = "Synthetic123!"
    assert runner.invoke(main, ["create-admin", "--email", "admin@example.org", "--name", "Admin"], input=f"{password}\n{password}\n").exit_code == 0
    import tomllib
    secret = tomllib.loads(config.read_text())["SECRET_KEY"]
    with config.open("a", encoding="utf-8") as stream:
        stream.write('\nENABLED_PLUGINS = ["missing_plugin"]\nSMTP_PASSWORD = "synthetic-secret"\n')
    database = tmp_path / "neofab2.sqlite3"
    before = database.read_bytes()
    result = runner.invoke(main, ["maintenance-info"])
    assert result.exit_code == 0
    assert "admin@example.org (active)" in result.output
    assert password not in result.output and secret not in result.output
    assert "synthetic-secret" not in result.output and "scrypt" not in result.output
    assert database.read_bytes() == before
