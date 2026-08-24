"""Characterization coverage for the extracted v5 argparse seam."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402
from extractor import cli_args  # noqa: E402


def test_runner_facade_returns_extracted_operator_parser_with_shared_defaults() -> None:
    parser = runner.build_parser()
    args = parser.parse_args([])

    assert isinstance(parser, cli_args.OperatorArgumentParser)
    assert runner.OperatorArgumentParser is cli_args.OperatorArgumentParser
    assert args.max_files_docs == cli_args.DEFAULT_MAX_FILES_DOCS
    assert args.max_files_code == cli_args.DEFAULT_MAX_FILES_CODE
    assert args.max_chars == cli_args.DEFAULT_MAX_CHARS
    assert args.file_truncate_chars == cli_args.DEFAULT_FILE_TRUNCATE_CHARS


def test_profile_budget_override_compares_against_cli_default_constants() -> None:
    source = inspect.getsource(runner.main)

    assert "args.max_files_docs == DEFAULT_MAX_FILES_DOCS" in source
    assert "args.max_files_code == DEFAULT_MAX_FILES_CODE" in source
    assert "args.max_chars == DEFAULT_MAX_CHARS" in source
    assert "args.file_truncate_chars == DEFAULT_FILE_TRUNCATE_CHARS" in source


def test_main_has_one_introspection_dispatch_block() -> None:
    source = inspect.getsource(runner.main)

    assert source.count("if args.print_config:") == 1
    assert source.count("if args.print_run_order:") == 1
    assert source.count("if args.print_phase_routing:") == 1
    assert source.count("if args.print_phase_prompts is not None:") == 1


def test_profile_budget_override_applies_when_parser_defaults_are_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured = {}
    profile = {
        "name": "test-profile",
        "version": "1",
        "phase_policy": {
            "enabled_phases": ["A"],
            "budgets_by_phase": {
                "A": {
                    "max_files": 3,
                    "max_chars": 300,
                    "file_truncate_chars": 30,
                }
            },
        },
    }

    def capture_manifest(*args, **kwargs):
        captured["args"] = args[3]
        raise SystemExit(0)

    monkeypatch.setattr(runner, "_load_extraction_profile", lambda _name: profile)
    monkeypatch.setattr(runner, "write_run_manifest", capture_manifest)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_extraction_v5.py",
            "--phase",
            "A",
            "--dry-run",
            "--skip-prescan",
            "--profile",
            "test-profile",
            "--output-root",
            str(tmp_path / "artifacts"),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.main()

    assert exc_info.value.code == 0
    args = captured["args"]
    assert args.max_files_docs == 3
    assert args.max_files_code == 3
    assert args.max_chars == 300
    assert args.file_truncate_chars == 30


def test_max_cost_usd_help_text_states_profile_default_applies_when_unset() -> None:
    """TP-RTE-TRUTH-R2-004 / F-14: the cost cap that actually applies at
    runtime is the active cost profile's default (auto-applied, see
    run_extraction_v5.py's "Applied cost-profile default --max-cost-usd="
    log line), not merely "the value you pass". --max-cost-usd's help text
    is the operator's only surfaced hint that a cap is *always* in effect
    -- it must say so, not just describe the flag as an opt-in override."""
    parser = runner.build_parser()

    max_cost_action = next(
        action for action in parser._actions if "--max-cost-usd" in action.option_strings
    )

    assert "cost profile's default cap is auto-applied" in max_cost_action.help
    assert "When unset" in max_cost_action.help
