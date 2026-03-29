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
    
    clean_ok, clean_detail = require_clean_worktree(repo_root)
    if getattr(args, "allow_dirty", False):
        overrides.append(
            OverrideRecord(
                override_type="allow_dirty",
                actor="cli",
                reason="User explicitly allowed dirty worktree execution.",
                scope="preflight.clean_worktree",
                source="--allow-dirty",
            )
        )
        checks.append(
            PreflightCheck(
                name="clean_worktree",
                status="warning" if not clean_ok else "passed",
                required=True,
                details=clean_detail,
                remediation="Clean the repo root or keep using `--allow-dirty` deliberately.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="clean_worktree",
                status="passed" if clean_ok else "failed",
                required=True,
                details=clean_detail,
                remediation="Commit or stash tracked changes before execute-mode runs.",
            )
        )
    for step in policy.get("validation", {}).get("steps", []):
        command = step.get("command", [])
        if command and len(command) > 1 and command[1].startswith("scripts/"):
            script_path = repo_root / command[1]
            checks.append(
                PreflightCheck(
                    name=f"script:{command[1]}",
                    status="passed" if script_path.exists() else "failed",
                    required=True,
                    details=str(script_path),
                    remediation=f"Restore or update `{command[1]}` in policy.",
                )
            )
    rate_limit = client.rate_limit_snapshot()
    precheck = PreflightResult(
        ok=all(item.status in {"passed", "warning"} for item in checks),
        checks=checks,
        policy_resolution=policy_artifact_payload(policy).get(
            "policy_resolution"
        ),  # placeholder, replaced below
        override_records=overrides,
    )
    precheck_payload = precheck.to_dict()
    precheck_payload["meta"] = artifact_meta(
        repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id
    ).to_dict()
    precheck_payload["policy_resolution"] = {
        "source": policy_artifact_payload(policy).get("policy_source", ""),
        "path": policy_artifact_payload(policy).get("policy_path", ""),
        "fingerprint": policy_artifact_payload(policy).get("policy_fingerprint", ""),
        "policy_schema_version": POLICY_SCHEMA_VERSION,
        "overrides": [item.to_dict() for item in overrides],
    }
    write_json(run_dir / "PRECHECK.json", precheck_payload)
    environment = snapshot_environment(repo_root)
    environment.update({"repo_slug": repo_slug, "rate_limit": rate_limit})
    write_json(run_dir / "ENVIRONMENT.json", environment)
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    if not getattr(args, "_suppress_output", False):
        if getattr(args, "json", False):
            print(json.dumps(precheck_payload, indent=2))
        else:
            print(f"Preflight artifacts: {run_dir}")
    return 0 if precheck.ok else 2
