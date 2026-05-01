from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from dopemux.cli import cli


def test_legacy_repscan_cli_is_disabled_with_canonical_replacement() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_repscan_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "repscan",
                "--promptgen",
                "v1",
                "--phase",
                "C",
                "--run-id",
                "RID123",
                "--promptgen-only",
            ],
        )

    assert result.exit_code != 0, result.output
    assert "dopemux rte scan" in result.output
    mocked.assert_not_called()


def test_rte_scan_invokes_runner_with_raw_args() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_repscan_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "rte",
                "scan",
                "--promptgen",
                "v1",
                "--phase",
                "C",
                "--run-id",
                "RID123",
                "--promptgen-only",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once_with(
        args=["--phase", "C", "--run-id", "RID123", "--promptgen", "v1", "--promptgen-only"]
    )
