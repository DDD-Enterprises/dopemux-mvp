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
    _run_v5(
        ["--status-json", "--run-id", "this_is_a_typo_xyz_status_json"],
        output_root=output_root,
    )
    created = list(output_root.rglob("*"))
    # Allow the output_root itself, but nothing inside
    assert not any(p.is_file() for p in created), (
        f"--status-json must not create files; got: {[str(p) for p in created]}"
    )
    assert not any(
        "runs" in p.parts for p in created
    ), f"--status-json must not create runs/ dirs; got: {[str(p) for p in created]}"


@pytest.mark.xfail(
    reason="FA-7-MED-1: --status (text) writes telemetry/TERMINAL_TIMELINE.jsonl under typo'd run-id. PR #603 fixed phase dirs but missed the telemetry sidecar."
)
def test_status_text_should_be_fully_readonly(tmp_path: Path) -> None:
    """xfail until --status (text) wraps telemetry writer in readonly_introspection."""
    output_root = tmp_path / "out"
    output_root.mkdir()
    _run_v5(
        ["--status", "--run-id", "this_is_a_typo_xyz_status_text"],
        output_root=output_root,
    )
    runs_dir = output_root / "runs"
    if not runs_dir.exists():
        return  # passes
    # Any directory or file under runs/ is a violation
    created = list(runs_dir.rglob("*"))
    assert not created, (
        f"--status with typo'd run-id should create ZERO files under runs/; "
        f"got: {[str(p) for p in created]}"
    )
