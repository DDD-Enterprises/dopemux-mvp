"""TP-RTE-TRUTH-R4-004 (F-43): `rte run` used to expose ONLY `--partition-
workers` (no short flag), while `audit wizard` already used the canonical
`--workers/-w` shape. This inverted `rte run` to match: `--workers/-w` is
now the visible, canonical flag; `--partition-workers` is a hidden
backward-compatible alias.

These tests invoke the REAL `dopemux` CLI via Click's CliRunner (not a
helper function in isolation) and intercept
`dopemux.cli._run_extractor_runner` -- the seam where `rte run` shells out
to run_extraction_v5.py -- to assert on the exact `--partition-workers`
value the wiring produces for each flag combination. No provider is ever
called: every invocation passes `--dry-run` and the runner itself is
monkeypatched to a recording stub, so nothing here executes
run_extraction_v5.py.
"""

from __future__ import annotations

from typing import List

import pytest
from click.testing import CliRunner

import dopemux.cli as dopemux_cli


@pytest.fixture()
def captured_runner_args(monkeypatch: pytest.MonkeyPatch) -> List[List[str]]:
    calls: List[List[str]] = []

    def _fake_run_extractor_runner(*, pipeline_version: str, args: List[str], repo_root=None) -> None:
        del pipeline_version, repo_root
        calls.append(list(args))

    monkeypatch.setattr(dopemux_cli, "_run_extractor_runner", _fake_run_extractor_runner)
    return calls


def _partition_workers_value(args: List[str]) -> str:
    idx = args.index("--partition-workers")
    return args[idx + 1]


def test_rte_run_help_shows_canonical_workers_short_flag() -> None:
    result = CliRunner().invoke(dopemux_cli.cli, ["rte", "run", "--help"])

    assert result.exit_code == 0
    assert "-w, --workers" in result.output
    # The legacy flag must NOT be advertised in --help (hidden=True).
    assert "--partition-workers" not in result.output


def test_rte_run_defaults_to_one_worker(captured_runner_args: List[List[str]]) -> None:
    result = CliRunner().invoke(dopemux_cli.cli, ["rte", "run", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert _partition_workers_value(captured_runner_args[0]) == "1"


def test_rte_run_accepts_canonical_long_flag(captured_runner_args: List[List[str]]) -> None:
    result = CliRunner().invoke(dopemux_cli.cli, ["rte", "run", "--dry-run", "--workers", "5"])

    assert result.exit_code == 0, result.output
    assert _partition_workers_value(captured_runner_args[0]) == "5"


def test_rte_run_accepts_canonical_short_flag(captured_runner_args: List[List[str]]) -> None:
    result = CliRunner().invoke(dopemux_cli.cli, ["rte", "run", "--dry-run", "-w", "6"])

    assert result.exit_code == 0, result.output
    assert _partition_workers_value(captured_runner_args[0]) == "6"


def test_rte_run_still_accepts_legacy_partition_workers_flag(
    captured_runner_args: List[List[str]],
) -> None:
    """Backward compatibility: --partition-workers must keep working even
    though it is now hidden from --help."""
    result = CliRunner().invoke(
        dopemux_cli.cli, ["rte", "run", "--dry-run", "--partition-workers", "7"]
    )

    assert result.exit_code == 0, result.output
    assert _partition_workers_value(captured_runner_args[0]) == "7"


def test_legacy_flag_wins_when_both_are_passed(captured_runner_args: List[List[str]]) -> None:
    """Mirrors _resolved_pipeline_version's precedence (--engine-version over
    --pipeline-version): an explicitly passed legacy flag wins, so an old
    script pinning --partition-workers=N keeps getting exactly N even if a
    caller also passes --workers."""
    result = CliRunner().invoke(
        dopemux_cli.cli,
        ["rte", "run", "--dry-run", "--workers", "5", "--partition-workers", "9"],
    )

    assert result.exit_code == 0, result.output
    assert _partition_workers_value(captured_runner_args[0]) == "9"


def test_resolved_partition_workers_helper_matches_wiring() -> None:
    resolver = dopemux_cli._resolved_partition_workers
    assert resolver(None, None) == 1
    assert resolver(5, None) == 5
    assert resolver(None, 7) == 7
    assert resolver(5, 9) == 9
