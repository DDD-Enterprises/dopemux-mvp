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


def test_rte_scan_refuses_without_legacy_v3_opt_in() -> None:
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

    assert result.exit_code != 0, result.output
    assert "disabled by default" in result.output
    mocked.assert_not_called()


def test_rte_scan_invokes_runner_with_raw_args_when_legacy_opt_in() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_repscan_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "rte",
                "scan",
                "--allow-legacy-v3-scan",
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
        args=[
            "--allow-legacy-v3-scan",
            "--phase",
            "C",
            "--run-id",
            "RID123",
            "--promptgen",
            "v1",
            "--promptgen-only",
        ]
    )
