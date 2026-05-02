"""Bundled proof writer for TP-OPS-MAC-SCRUBBER-001."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .models import ProofBundle, ToolReport, stable_json, utc_now


TP_ID = "TP-OPS-MAC-SCRUBBER-001"


def git_state(repo_root: Path) -> dict[str, Any]:
    def run(args: list[str]) -> str:
        proc = subprocess.run(args, cwd=repo_root, capture_output=True, text=True, check=False)
        return proc.stdout.strip()

    head = run(["git", "rev-parse", "HEAD"])
    return {
        "branch": run(["git", "branch", "--show-current"]) or "HEAD",
        "head": head,
        "head_before": head,
        "head_after": head,
        "commits": [],
        "status_short": run(["git", "status", "--short"]),
    }


def write_proof(
    proof_path: Path,
    *,
    repo_root: Path,
    tool_report: ToolReport,
    implementation: dict[str, Any],
    tests: dict[str, Any],
    runtime_validation: dict[str, Any],
    docs: dict[str, Any],
    acceptance: dict[str, Any],
    unresolved: list[str],
) -> ProofBundle:
    bundle = ProofBundle(
        tp_id=TP_ID,
        repo="dopemux-mvp",
        schema_version="system-data-proof.v1",
        timestamp_utc=utc_now(),
        git=git_state(repo_root),
        tool_report=tool_report,
        implementation=implementation,
        tests=tests,
        runtime_validation=runtime_validation,
        docs=docs,
        acceptance=acceptance,
        unresolved=unresolved,
    )
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(stable_json(bundle), encoding="utf-8")
    return bundle
