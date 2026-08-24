"""
FA-7-MED-1 — `--status` (text-output mode) writes telemetry/TERMINAL_TIMELINE.jsonl
under a typo'd run-id, violating the readonly_introspection contract.

This is a partial regression of the P5 F4-CRIT-1 fix. PR #603 closed the
14 phantom phase dirs but missed the telemetry sidecar in `--status` text
mode. `--status-json` is clean.

Documented in: rte_audit_findings_FA7_preextractor.md / FA-7-MED-1
xfail until the telemetry writer is wrapped in `if not readonly_introspection:`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_SERVICE_ROOT = Path(__file__).resolve().parents[3]
_RUNNER = _SERVICE_ROOT / "run_extraction_v5.py"


def _run_v5(args: list[str], output_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(_RUNNER),
            *args,
            "--output-root",
            str(output_root),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_status_json_is_fully_readonly(tmp_path: Path) -> None:
    """Positive regression: --status-json with typo'd run-id creates ZERO files."""
    output_root = tmp_path / "out"
    output_root.mkdir()
    result = _run_v5(
        ["--status-json", "--run-id", "this_is_a_typo_xyz_status_json"],
        output_root=output_root,
    )
    assert result.returncode == 0, result.stderr
    created = list(output_root.rglob("*"))
    # Allow the output_root itself, but nothing inside
    assert not any(p.is_file() for p in created), (
        f"--status-json must not create files; got: {[str(p) for p in created]}"
    )
    assert not any(
        "runs" in p.parts for p in created
    ), f"--status-json must not create runs/ dirs; got: {[str(p) for p in created]}"


def test_status_text_should_be_fully_readonly(tmp_path: Path) -> None:
    """FA-7-MED-1 / TP-RTE-TRUTH-R2-005: --status (text) must not write
    telemetry/TERMINAL_TIMELINE.jsonl under a typo'd run-id.

    Fixed by `UI._emit_event` honoring a `readonly` flag (threaded from
    `main()`'s `readonly_introspection` through the `UI(...)` construction
    at the --status/--status-json dispatch site), landed alongside F-59's
    related `resolve_run_context(resolve_latest_when_readonly=...)` work in
    run_extraction_v5.py / extractor/ui.py / rte_output_layout.py. Verified
    by mutation: reverting those three files to HEAD reproduces the phantom
    `runs/<typo'd-id>/telemetry/TERMINAL_TIMELINE.jsonl` write and fails this
    assertion; restoring them makes it pass again."""
    output_root = tmp_path / "out"
    output_root.mkdir()
    result = _run_v5(
        ["--status", "--run-id", "this_is_a_typo_xyz_status_text"],
        output_root=output_root,
    )
    assert result.returncode == 0, result.stderr
    runs_dir = output_root / "runs"
    if not runs_dir.exists():
        return  # passes
    # Any directory or file under runs/ is a violation
    created = list(runs_dir.rglob("*"))
    assert not created, (
        f"--status with typo'd run-id should create ZERO files under runs/; "
        f"got: {[str(p) for p in created]}"
    )
