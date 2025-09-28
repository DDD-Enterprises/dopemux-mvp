from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from chatx.cli.main import app


runner = CliRunner()


def test_backup_missing_manifest_hints_mobilesync(tmp_path: Path) -> None:
    # Create backup-like dir without Manifest.db
    backup_dir = tmp_path / "MissingManifest"
    backup_dir.mkdir(parents=True)

    result = runner.invoke(
        app,
        [
            "imessage",
            "pull",
            "--contact",
            "+15551230000",
            "--from-backup",
            str(backup_dir),
            "--out",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code != 0
    assert "Manifest.db not found" in result.stdout
    assert "MobileSync/Backup" in result.stdout


def test_backup_wrong_path_shows_hint(tmp_path: Path) -> None:
    # Path does not exist
    backup_dir = tmp_path / "DoesNotExist"

    result = runner.invoke(
        app,
        [
            "imessage",
            "pull",
            "--contact",
            "+15551230000",
            "--from-backup",
            str(backup_dir),
            "--out",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code != 0
    assert "Backup directory not found" in result.stdout
    assert "MobileSync/Backup" in result.stdout

