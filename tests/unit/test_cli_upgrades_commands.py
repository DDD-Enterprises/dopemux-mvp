from __future__ import annotations

import os
from unittest.mock import patch

import click
from click.testing import CliRunner

from dopemux.cli import cli, rte, upgrades


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


def test_upgrades_run_rejects_prescan_flags_for_v4() -> None:
    runner = CliRunner()

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
            "--skip-prescan",
        ],
    )

    assert result.exit_code != 0
    assert "only supported with --version v5" in result.output


def test_rte_wizard_alias_exposes_audit_wizard_options() -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "rte",
            "wizard",
            "--help",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "guided extraction flight-deck walkthrough" in result.output.lower()
    assert "--routing-policy" in result.output
    assert "--educate / --no-educate" in result.output
    assert "--execute" in result.output


def test_upgrades_run_forwards_prescan_flags_for_v5() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs("prescan", exist_ok=True)
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
                    "--skip-prescan",
                    "--prescan-import-dir",
                    "prescan",
                    "--prescan-online",
                    "--prescan-allow-scope-reduction",
                    "--allow-online-llm",
                ],
            )

    assert result.exit_code == 0, result.output
    args = mocked.call_args.kwargs["args"]
    assert "--skip-prescan" in args
    assert "--prescan-import-dir" in args
    assert "prescan" in args
    assert "--prescan-online" in args
    assert "--prescan-allow-scope-reduction" in args
    assert "--allow-online-llm" in args


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

def test_extractor_alias_is_disabled_for_runtime_status() -> None:
    runner = CliRunner()
    with patch("dopemux.commands.extractor_commands._run_extractor_runner") as mocked:
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

    assert result.exit_code != 0, result.output
    assert "dopemux rte status" in result.output
    mocked.assert_not_called()


def test_upgrades_trace_routes_to_v5_dry_run_alias() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "upgrades",
                "trace",
                "--phase",
                "C",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once_with(
        pipeline_version="v5",
        args=["--phase", "C", "--dry-run"],
    )


def test_rte_trace_execute_forwards_execute_flag_explicitly() -> None:
    """TP-RTE-TRUTH-R4-004 (F-44, item 5): `rte trace --execute` must forward
    `--execute` explicitly to the v5 runner (mirroring `rte run`'s
    `--dry-run/--execute` pattern), not merely omit `--dry-run` and rely on
    run_extraction_v5.py's own `args.execute = bool(args.execute or not
    args.dry_run)` normalization to imply it. Both paths reach the same
    DPMX_LIVE_OK consent gate, but the explicit forward keeps the safety
    property visible at this call site instead of depending on an
    incidental downstream normalization line.
    """
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "rte",
                "trace",
                "--execute",
                "--phase",
                "C",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once_with(
        pipeline_version="v5",
        args=["--phase", "C", "--execute"],
    )


def test_truth_command_is_deprecated() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["truth"])
    assert result.exit_code != 0
    assert "`dopemux truth` is not a supported Repo Truth Extractor entrypoint" in result.output


def test_truth_command_rejects_legacy_deep_mode() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["truth", "--deep"])

    assert result.exit_code != 0
    assert "`dopemux truth` is not a supported Repo Truth Extractor entrypoint" in result.output


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


def test_rte_run_forwards_cost_profile_controls() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner") as mocked:
        result = runner.invoke(
            cli,
            [
                "rte",
                "run",
                "--pipeline-version",
                "v5",
                "--phase",
                "A",
                "--dry-run",
                "--cost-profile",
                "rte-cost-balanced",
                "--model-alias",
                "SYNTH_MODEL=openai/gpt-5.5",
                "--disable-provider",
                "openai",
                "--max-cost-usd",
                "12.5",
                "--routing-policy",
                "balanced_openrouter",
            ],
        )

    assert result.exit_code == 0, result.output
    mocked.assert_called_once()
    args = mocked.call_args.kwargs["args"]
    assert "--cost-profile" in args and "rte-cost-balanced" in args
    assert "--model-alias" in args and "SYNTH_MODEL=openai/gpt-5.5" in args
    assert "--disable-provider" in args and "openai" in args
    assert "--max-cost-usd" in args and "12.5" in args
    policy_index = args.index("--routing-policy")
    assert args[policy_index + 1] == "balanced_openrouter"


def test_rte_run_help_lists_cost_profile_controls() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["rte", "run", "--help"])
    assert result.exit_code == 0, result.output
    for flag in ("--cost-profile", "--model-alias", "--disable-provider", "--max-cost-usd"):
        assert flag in result.output


# ─────────────────────────────────────────────────────────────────────────
# TP-RTE-TRUTH-R4-002 (F-42): definition-site inversion — `rte` is now the
# canonical definition site; `upgrades` is a hidden, deprecated alias that
# must remain fully functional. These tests assert against the *actual*
# click.Group registry produced by importing dopemux.cli (the real wiring),
# not against helper functions in isolation.
# ─────────────────────────────────────────────────────────────────────────

# Commands that were reachable as `dopemux upgrades <x>` before the
# inversion (per claudedocs/rte-truth-program-2026-07/A4-cli-ux-docs.md
# §1.2). Backward compatibility requires every one of these to still
# resolve on the post-inversion `upgrades` group.
_PRE_INVERSION_UPGRADES_COMMANDS = frozenset(
    {"list", "run", "doctor", "status", "preflight", "validate-live", "trace", "promptset"}
)


def test_upgrades_is_hidden_and_rte_is_canonical_in_top_level_help() -> None:
    """`rte` is the visible canonical group; `upgrades` must not appear in
    top-level help (it is a deprecated alias, not a first-class surface)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.output
    assert "rte" in result.output
    # Match on a full CLI-token boundary so this can't accidentally match
    # substrings like "upgradesomething" in unrelated help text.
    assert not any(
        line.strip().startswith("upgrades ") or line.strip() == "upgrades"
        for line in result.output.splitlines()
    )
    assert upgrades.hidden is True


def test_upgrades_alias_group_has_full_parity_with_rte_registry() -> None:
    """Enumerate the *entire* alias group's command registry (not a
    hand-picked sample) and assert each entry is the literal same
    click.Command/click.Group object registered under `rte` — i.e. the
    alias cannot silently drift from the canonical definition, and nothing
    that used to be reachable under `upgrades` was dropped."""
    # Nothing that was reachable pre-inversion may have disappeared.
    assert _PRE_INVERSION_UPGRADES_COMMANDS <= set(upgrades.commands.keys())

    # Every command currently registered on the alias group must be the
    # identical object registered on the canonical group -- not a re-
    # implementation, not a stale copy.
    assert set(upgrades.commands.keys()) <= set(rte.commands.keys())
    for name, alias_command in upgrades.commands.items():
        canonical_command = rte.commands[name]
        assert alias_command is canonical_command, (
            f"`upgrades {name}` is not the same object as `rte {name}`; "
            "the alias has drifted from the canonical definition."
        )

        if isinstance(alias_command, click.Group):
            # Recurse: sub-groups (promptset) must have full parity too,
            # not just a partial/legacy subset.
            assert set(alias_command.commands.keys()) == set(
                canonical_command.commands.keys()
            ), (
                f"`upgrades {name}` subcommands "
                f"{sorted(alias_command.commands.keys())} do not match "
                f"`rte {name}` subcommands "
                f"{sorted(canonical_command.commands.keys())}."
            )
            for sub_name, sub_alias_command in alias_command.commands.items():
                assert sub_alias_command is canonical_command.commands[sub_name]


def test_upgrades_invoke_emits_deprecation_warning() -> None:
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner"):
        result = runner.invoke(
            cli, ["upgrades", "list", "--pipeline-version", "v5"]
        )

    assert result.exit_code == 0, result.output
    assert "deprecated alias" in result.output
    assert "dopemux rte" in result.output

    # Paired same-process check: Click only invokes a group's callback when
    # a subcommand actually runs, so `--help` on the bare group must stay
    # quiet even though the callback (proven above to warn) is the same
    # object for every invocation path.
    help_result = runner.invoke(cli, ["upgrades", "--help"])
    assert help_result.exit_code == 0, help_result.output
    assert "deprecated alias" not in help_result.output


def test_rte_invoke_does_not_leak_deprecation_warning() -> None:
    """The deprecation warning lives on the `upgrades` group callback only;
    invoking the same underlying command through the canonical `rte` group
    must never surface it, even though the Command object is shared."""
    runner = CliRunner()
    with patch("dopemux.cli._run_extractor_runner"):
        result = runner.invoke(cli, ["rte", "list", "--pipeline-version", "v5"])

    assert result.exit_code == 0, result.output
    assert "deprecated alias" not in result.output
