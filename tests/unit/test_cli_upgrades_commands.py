from __future__ import annotations

import os
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


def test_upgrades_run_forwards_batch_control_flags() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "run",
                "--pipeline-version",
                "v5",
                "--phase",
                "C",
                "--step",
                "C1",
                "--batch-submit-only",
                "--batch-watch",
                "--batch-retrieve",
                "--batch-ids",
                "job-1",
                "--batch-ids",
                "job-2",
                "--retrieve-provider",
                "xai",
                "--max-partitions-per-step",
                "3",
                "--s-steps",
                "S0,S1",
                "--allow-multi-phase-live-batch",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    args = mocked.call_args.kwargs["args"]
    assert "--step" in args and "C1" in args
    assert "--s-steps" in args and "S0,S1" in args
    assert "--batch-submit-only" in args
    assert "--batch-watch" in args
    assert "--batch-retrieve" in args
    assert args.count("--batch-ids") == 2
    retrieve_index = args.index("--retrieve-provider")
    assert args[retrieve_index + 1] == "xai"
    max_partitions_index = args.index("--max-partitions-per-step")
    assert args[max_partitions_index + 1] == "3"
    assert "--allow-multi-phase-live-batch" in args


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


def test_upgrades_run_accepts_v5_pipeline_version() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "run",
                "--pipeline-version",
                "v5",
                "--phase",
                "A",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    assert kwargs["pipeline_version"] == "v5"


def test_upgrades_run_defaults_routing_policy_to_openrouter_for_v5() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "run",
                "--pipeline-version",
                "v5",
                "--phase",
                "A",
                "--dry-run",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    args = kwargs["args"]
    policy_index = args.index("--routing-policy")
    assert args[policy_index + 1] == "balanced_openrouter"


def test_upgrades_run_defaults_routing_policy_to_cost_for_v4() -> None:
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
                "--dry-run",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    args = kwargs["args"]
    policy_index = args.index("--routing-policy")
    assert args[policy_index + 1] == "cost"


def test_upgrades_run_accepts_openrouter_routing_policy_choice() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "run",
                "--pipeline-version",
                "v5",
                "--phase",
                "A",
                "--dry-run",
                "--routing-policy",
                "openrouter",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    args = kwargs["args"]
    policy_index = args.index("--routing-policy")
    assert args[policy_index + 1] == "openrouter"


def test_upgrades_run_forwards_promptset_root() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("promptset.yaml", "w", encoding="utf-8") as handle:
            handle.write("steps: []\n")
        with patch("dopemux.cli._run_extractor_runner") as mocked:
            result = runner.invoke(
                cli,
                [
                    "upgrades",
                    "run",
                    "--pipeline-version",
                    "v5",
                    "--phase",
                    "A",
                    "--dry-run",
                    "--promptset-root",
                    ".",
                ],
            )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    assert "--promptset-root" in kwargs["args"]
    assert "." in kwargs["args"]


<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
def test_upgrades_run_rejects_openrouter_batch_provider_choice() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "upgrades",
            "run",
            "--pipeline-version",
            "v5",
            "--phase",
            "A",
            "--dry-run",
            "--batch-provider",
            "openrouter",
        ],
    )

    assert result.exit_code != 0
    assert "openrouter" in result.output


<<<<<<< Updated upstream
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


def test_upgrades_preflight_forwards_promptset_root_to_preflight_and_auth_doctor() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("promptset.yaml", "w", encoding="utf-8") as handle:
            handle.write("steps: []\n")
        with patch("dopemux.cli._run_extractor_runner") as mocked:
            result = runner.invoke(
                cli,
                [
                    "upgrades",
                    "preflight",
                    "--pipeline-version",
                    "v5",
                    "--promptset-root",
                    ".",
                    "--auth-doctor",
                ],
            )

    assert result.exit_code == 0, result.output
    assert mocked.call_count == 2
    for call in mocked.call_args_list:
        assert "--promptset-root" in call.kwargs["args"]
        assert "." in call.kwargs["args"]


def test_upgrades_validate_live_invokes_validation_runner() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        promptset_root = "promptset"
        os.makedirs(promptset_root, exist_ok=True)
        for name in ("promptset.yaml", "artifacts.yaml", "model_map.yaml"):
            path = f"{promptset_root}/{name}"
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{}\n")
        with patch("dopemux.cli.run_live_validation") as mocked:
            mocked.return_value = {"status": "pass", "run_id": "validation_001"}
            result = runner.invoke(
                cli,
                [
                    "upgrades",
                    "validate-live",
<<<<<<< Updated upstream
                    "--stage",
                    "provider_probe",
                    "--promptset-root",
                    promptset_root,
                ],
            )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()


def test_upgrades_validate_live_fails_when_runner_reports_blockers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        promptset_root = "promptset"
        os.makedirs(promptset_root, exist_ok=True)
        for name in ("promptset.yaml", "artifacts.yaml", "model_map.yaml"):
            path = f"{promptset_root}/{name}"
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{}\n")
        with patch("dopemux.cli.run_live_validation") as mocked:
            mocked.return_value = {
                "status": "fail",
                "run_id": "validation_002",
                "blockers": ["repo_local_cli_origin: stale install"],
            }
            result = runner.invoke(
                cli,
                [
                    "upgrades",
                    "validate-live",
                    "--promptset-root",
                    promptset_root,
                ],
            )

    assert result.exit_code != 0
    assert "repo_local_cli_origin: stale install" in result.output
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes


def test_upgrades_validate_live_accepts_phase_slice_stage_and_provider() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        promptset_root = "promptset"
        os.makedirs(promptset_root, exist_ok=True)
        for name in ("promptset.yaml", "artifacts.yaml", "model_map.yaml"):
            path = f"{promptset_root}/{name}"
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{}\n")
        with open("pricing.json", "w", encoding="utf-8") as handle:
            handle.write('{"route_call_upper_bounds":{"openai/gpt-5-mini":0.1}}\n')
        with patch("dopemux.cli.run_live_validation") as mocked:
            mocked.return_value = {"status": "pass", "run_id": "validation_003"}
            result = runner.invoke(
                cli,
                [
                    "upgrades",
                    "validate-live",
                    "--stage",
                    "phase_slice",
                    "--provider",
                    "xai",
                    "--pricing-manifest",
                    "pricing.json",
                    "--promptset-root",
                    promptset_root,
                ],
            )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    config = mocked.call_args.args[0]
    assert config.stage == "phase_slice"
    assert config.selected_provider == "xai"
<<<<<<< Updated upstream
