from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from dopemux.cli import cli


def test_upgrades_run_forwards_pipeline_version_and_ui_flags() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "run",
                "--pipeline-version",
                "v4",
                "--phase",
                "A",
                "--run-id",
                "rid1",
                "--dry-run",
                "--resume",
                "--ui",
                "rich",
                "--pretty",
                "--quiet",
                "--jsonl-events",
                "--batch-mode",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    assert kwargs["pipeline_version"] == "v4"
    assert "--ui" in kwargs["args"]
    assert "rich" in kwargs["args"]
    assert "--pretty" in kwargs["args"]
    assert "--quiet" in kwargs["args"]
    assert "--jsonl-events" in kwargs["args"]
    assert "--batch-mode" in kwargs["args"]


def test_upgrades_run_accepts_engine_version_alias() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "run",
                "--engine-version",
                "v3",
                "--phase",
                "A",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    assert kwargs["pipeline_version"] == "v3"


def test_extractor_alias_warns_and_executes() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "extractor",
                "status",
                "--pipeline-version",
                "v4",
                "--run-id",
                "rid2",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "legacy" in result.output.lower()
    mocked.assert_called_once()


def test_upgrades_promptset_audit_routes_to_v4_runner() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "promptset",
                "audit",
                "--pipeline-version",
                "v4",
                "--strict",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once_with(
        pipeline_version="v4",
        args=["--promptset-audit", "--strict-audit"],
    )
