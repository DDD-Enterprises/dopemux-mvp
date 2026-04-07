from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
import time
from collections import defaultdict, deque
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .classification import (
    CLASS_PRIORITY,
    VALID_TRANSITIONS,
    _severity_value,
    _state_value,
    _status_value,
    build_pr_state,
    classify_pr,
    ensure_transition,
    has_conflicts,
    lifecycle_for_findings,
    risk_score,
)
from .github_api import (
    BOT_AUTHORS,
    GitHubClient,
    ci_status,
    summarize_checks,
    thread_counters,
)
from .policy import (
    PolicyError,
    load_effective_policy,
    policy_artifact_payload,
    policy_fingerprint,
)
from .queue import (
    QUEUE_LOCK_PATH,
    acquire_queue_lock,
    apply_priority_preferences,
    build_dependency_edges,
    parse_pr_id_args,
    priority_key,
    release_queue_lock,
    require_clean_worktree,
    snapshot_payload,
    sort_states,
)
from .runtime import (
    CommandResult,
    append_command_log,
    execute_or_dry_run,
    fingerprint_payload,
    pid_is_running,
    run_command,
    run_id,
    shell_join,
    snapshot_environment,
    utc_now,
    write_json,
    write_text,
)
from .schema import (
    ARTIFACT_VERSION,
    POLICY_SCHEMA_VERSION,
    TOOL_VERSION,
    ArtifactMeta,
    BlockerType,
    FallbackReason,
    Finding,
    FindingSeverity,
    Fingerprint,
    MergeActionType,
    MergeDecision,
    OverrideRecord,
    PhaseRecord,
    PolicyResolution,
    PreflightCheck,
    PreflightResult,
    PRResult,
    PRState,
    PRStateData,
    PullRequestState,
    QueueOrderingLayer,
    ReviewThread,
    RunManifest,
    ThreadComment,
    ThreadDisposition,
    ThreadDispositionType,
    TruthSource,
    ValidationReport,
    ValidationStatus,
)
from .strategy_library import STRATEGY_LIBRARY
from .validation import run_validation, validation_report_md

__all__ = [
    "preflight",
    "manifest_for_run",
    "write_manifest",
    "build_run_paths",
    "pr_dir_for",
]


def build_run_paths(out_dir: str, active_run_id: str) -> Tuple[Path, Path, Path]:
    run_dir = Path(out_dir) / f"run_{active_run_id}"
    queue_dir = run_dir / "queue"
    pr_root = run_dir / "pr"
    queue_dir.mkdir(parents=True, exist_ok=True)
    pr_root.mkdir(parents=True, exist_ok=True)
    return run_dir, queue_dir, pr_root


def pr_dir_for(pr_root: Path, pr_id: int) -> Path:
    path = pr_root / str(pr_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_for_run(
    *,
    active_run_id: str,
    mode: str,
    repo_root: Path,
    repo_slug: str,
    policy: Dict[str, Any],
) -> RunManifest:
    return RunManifest(
        run_id=active_run_id,
        mode=mode,
        repo_root=str(repo_root),
        repo_slug=repo_slug,
        policy_fingerprint=policy_fingerprint(policy),
        artifact_schema_versions={
            "artifact_version": ARTIFACT_VERSION,
            "tool_version": TOOL_VERSION,
            "policy_schema_version": str(POLICY_SCHEMA_VERSION),
        },
        completed_phases=[],
        resumable_phases=[
            "queue-scan",
            "pr-plan",
            "pr-apply",
            "pr-merge",
            "queue-drain",
        ],
        invalidation_conditions=[
            "policy fingerprint changes",
            "planned PR head SHA changes",
            "planned PR base SHA changes",
            "review state changes",
        ],
        pr_states={},
        artifact_pointers={},
    )


def write_manifest(run_dir: Path, manifest: RunManifest) -> None:
    write_json(run_dir / "RUN_MANIFEST.json", manifest.to_dict())


def preflight(args: argparse.Namespace) -> int:
    from .plan_builder import artifact_meta

    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, _ = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(
        repo_root, explicit_path=getattr(args, "policy", None)
    )
    meta = policy.get("_meta", {})
    policy_resolution = PolicyResolution(
        source=meta.get("source", "unknown"),
        path=meta.get("path", ""),
        fingerprint=meta.get("fingerprint", ""),
    )
    client = GitHubClient(
        repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy
    )
    repo_slug = client.resolve_repo_slug()
    binaries = ["git", "gh", "python", "pre-commit"]
    checks: List[PreflightCheck] = []
    overrides: List[OverrideRecord] = []
    for binary in binaries:
        result = run_command(["which", binary], cwd=repo_root, timeout_seconds=30)
        checks.append(
            PreflightCheck(
                name=f"binary:{binary}",
                status="passed" if result.returncode == 0 else "failed",
                required=True,
                details=result.stdout.strip() or result.stderr.strip(),
                remediation=f"Install `{binary}` and ensure it is on PATH.",
            )
        )
    auth = run_command(["gh", "auth", "status"], cwd=repo_root, timeout_seconds=60)
    checks.append(
        PreflightCheck(
            name="gh_auth",
            status="passed" if auth.returncode == 0 else "failed",
            required=True,
            details=auth.stdout.strip() or auth.stderr.strip(),
            remediation="Run `gh auth login` for the target repository.",
        )
    )
    remote = run_command(
        ["git", "remote", "get-url", "origin"], cwd=repo_root, timeout_seconds=30
    )
    checks.append(
        PreflightCheck(
            name="git_remote",
            status="passed" if remote.returncode == 0 else "failed",
            required=True,
            details=remote.stdout.strip() or remote.stderr.strip(),
            remediation="Configure the `origin` remote.",
        )
    )
    worktree = run_command(
        ["git", "worktree", "list"], cwd=repo_root, timeout_seconds=60
    )
    checks.append(
        PreflightCheck(
            name="git_worktree",
            status="passed" if worktree.returncode == 0 else "failed",
            required=True,
            details=worktree.stdout.strip() or worktree.stderr.strip(),
            remediation="Use a git version with worktree support.",
        )
    )
    
    ignore_case = run_command(
        ["git", "config", "--get", "core.ignorecase"], cwd=repo_root, timeout_seconds=30
    )
    is_ignore_case = ignore_case.stdout.strip().lower() == "true"
    checks.append(
        PreflightCheck(
            name="git_ignorecase",
            status="warning" if is_ignore_case else "passed",
            required=False,
            details=f"core.ignorecase={ignore_case.stdout.strip()}",
            remediation="Git case-insensitivity detected. Some renames might require `git mv` to be detected on this OS.",
        )
    )

    ok = all(c.status == "passed" or not c.required for c in checks)
    precheck = PreflightResult(
        ok=ok,
        checks=checks,
        policy_resolution=policy_resolution,
        override_records=overrides,
    )

    if run_dir and active_run_id:
        manifest = manifest_for_run(
            active_run_id=active_run_id,
            mode=getattr(args, "mode", "preflight"),
            repo_root=repo_root,
            repo_slug=repo_slug,
            policy=policy,
        )
        write_manifest(run_dir, manifest)
        write_json(run_dir / "PREFLIGHT_RESULT.json", precheck.to_dict())

    return 0 if precheck.ok else 2
