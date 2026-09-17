"""X01: Optionalen Test aus fremdem Arbeitsverzeichnis isoliert prüfen."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

BASH = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe") if os.name == "nt" else shutil.which("bash")
pytestmark = pytest.mark.skipif(not BASH or not Path(BASH).is_file(), reason="Bash nicht verfügbar")


@pytest.mark.parametrize("choice,status", [("n", 0), ("j", 0), ("j", 3), ("j", 130)])
def test_optional_start_preserves_installation_result(tmp_path, choice, status):
    installer = Path(__file__).resolve().parents[2] / "script/setupNeoFab"
    # Nur den Abschluss ausführen, keine OS-Installation simulieren oder starten.
    tail = installer.read_text(encoding="utf-8").split("printf 'Basisinstallation erfolgreich.", 1)[1]
    script = tmp_path / "test-start.sh"
    app = tmp_path / "application with spaces"
    app.mkdir()
    script.write_text(r'''
set -Eeuo pipefail
trap 'echo "Installation abgebrochen" >&2' ERR
APP_DIR="$TEST_APP"
CONFIG_FILE="$TEST_APP/config.toml"
PORT=8080
prompt() { printf -v "$1" '%s' "$TEST_CHOICE"; }
as_app() {
  pwd -P > "$TEST_LOG"
  return "$TEST_STATUS"
}
''' + "printf 'Basisinstallation erfolgreich." + tail, encoding="utf-8")
    log = tmp_path / "cwd.txt"
    result = subprocess.run(
        [BASH, script.as_posix()], cwd=tmp_path, capture_output=True, text=True,
        env={**os.environ, "TEST_APP": app.as_posix(), "TEST_LOG": log.as_posix(),
             "TEST_CHOICE": choice, "TEST_STATUS": str(status)},
    )
    assert "Basisinstallation erfolgreich" in result.stdout
    assert "Installation abgebrochen" not in result.stderr
    assert result.returncode == (status if choice == "j" and status not in (0, 130) else 0)
    if choice == "n":
        assert not log.exists()
    else:
        # Git Bash meldet /c/... statt C:/...; entscheidend ist der Zielordner.
        assert log.read_text().strip().endswith("/application with spaces")
        if status == 3:
            assert "Optionaler Teststart fehlgeschlagen" in result.stderr
            assert "keine Neuinstallation erforderlich" in result.stderr
        if status == 130:
            assert "Strg+C beendet" in result.stdout
