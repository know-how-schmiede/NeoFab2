"""X02/X03/N05: generated units and lifecycle, without touching host systemd."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(not BASH, reason="Bash unavailable")


@pytest.mark.parametrize("existing", [False, True])
def test_mail_units_and_idempotent_setup(tmp_path, existing):
    common = Path(__file__).resolve().parents[2] / "script/common.sh"
    unit = tmp_path / "neofab2-mail.service"
    timer = tmp_path / "neofab2-mail.timer"
    if existing:
        unit.write_text("WorkingDirectory=/opt/neofab2\nUser=neofab2\n# custom\n")
        timer.write_text("# custom timer\n")
    script = tmp_path / "test.sh"
    script.write_text(common.read_text() + r'''
MAIL_UNIT="$TEST_ROOT/neofab2-mail.service"
MAIL_TIMER_UNIT="$TEST_ROOT/neofab2-mail.timer"
systemctl() { echo "$*" >> "$TEST_ROOT/log"; }
systemd-analyze() { echo "$*" >> "$TEST_ROOT/log"; }
install_mail_worker
stop_mail_worker
''')
    result = subprocess.run([BASH, str(script)], capture_output=True, text=True,
                            env={**os.environ, "TEST_ROOT": str(tmp_path)})
    assert result.returncode == 0, result.stderr
    if existing:
        assert unit.read_text().endswith("# custom\n")
        assert timer.read_text() == "# custom timer\n"
    else:
        assert "User=neofab2\n" in unit.read_text()
        assert "mail-worker --limit 20" in unit.read_text()
        assert "Environment=NEOFAB2_CONFIG=/etc/neofab2/config.toml" in unit.read_text()
        assert "OnUnitInactiveSec=30s" in timer.read_text()
        assert "Unit=neofab2-mail.service" in timer.read_text()
    log = (tmp_path / "log").read_text()
    assert "enable --now neofab2-mail.timer" in log
    assert log.index("stop neofab2-mail.timer") < log.index("stop neofab2-mail.service")
