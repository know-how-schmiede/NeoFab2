"""X03/X07: CLI, konsistente Sicherung und Wiederherstellung mit Testdaten."""

import sqlite3
import tomllib

from click.testing import CliRunner

from neofab2.cli import main


def test_configuration_migration_backup_restore(tmp_path, monkeypatch):
    runner = CliRunner()
    config = tmp_path / "config.toml"
    data = tmp_path / "data"
    result = runner.invoke(main, ["init-config", "--output", str(config), "--data-dir", str(data)])
    assert result.exit_code == 0, result.output
    original = config.read_bytes()
    values = tomllib.loads(original.decode())
    assert len(values["SECRET_KEY"]) == 64
    assert values["SECRET_KEY"] not in result.output
    assert runner.invoke(main, ["init-config", "--output", str(config), "--data-dir", str(data)]).exit_code == 1
    assert config.read_bytes() == original
    monkeypatch.setenv("NEOFAB2_CONFIG", str(config))
    assert runner.invoke(main, ["check"]).exit_code == 1
    assert runner.invoke(main, ["migrate"]).exit_code == 0
    assert runner.invoke(main, ["check"]).exit_code == 0
    db_path = data / "neofab2.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.execute("INSERT INTO core_settings VALUES ('example', 'before')")
    backup = tmp_path / "backup.sqlite3"
    result = runner.invoke(main, ["backup", "--output", str(backup)])
    assert result.exit_code == 0, result.output
    assert runner.invoke(main, ["backup", "--output", str(backup)]).exit_code == 1
    with sqlite3.connect(db_path) as db:
        db.execute("UPDATE core_settings SET value='after'")
    # Restore into a different directory, never overwrite a live DB in the test.
    restored = tmp_path / "restored"
    restored.mkdir()
    (restored / "neofab2.sqlite3").write_bytes(backup.read_bytes())
    restore_config = tmp_path / "restore.toml"
    assert runner.invoke(main, ["init-config", "--output", str(restore_config), "--data-dir", str(restored)]).exit_code == 0
    monkeypatch.setenv("NEOFAB2_CONFIG", str(restore_config))
    assert runner.invoke(main, ["check"]).exit_code == 0
    with sqlite3.connect(restored / "neofab2.sqlite3") as db:
        assert db.execute("SELECT value FROM core_settings").fetchone() == ("before",)


def test_missing_configuration_returns_useful_cli_error(tmp_path, monkeypatch):
    monkeypatch.setenv("NEOFAB2_CONFIG", str(tmp_path / "missing.toml"))
    result = CliRunner().invoke(main, ["check"])
    assert result.exit_code == 1
    assert "NEOFAB2_CONFIG" in result.output


def test_relative_data_directory_rejected(tmp_path):
    result = CliRunner().invoke(main, ["init-config", "--output", str(tmp_path / "config.toml"), "--data-dir", "relative"])
    assert result.exit_code == 1
