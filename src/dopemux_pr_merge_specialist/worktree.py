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
    "prepare_worktree",
    "cleanup_worktree",
    "ensure_worktree_matches_pr_head",
    "attempt_rebase",
]


def prepare_worktree(
    repo_root: Path,
    pr_id: int,
    active_run_id: str,
    commands_log: Path,
    policy: Dict[str, Any],
) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    branch = f"prmerge/{active_run_id}-{pr_id}"
    path = Path("/tmp") / f"dopemux-pr-merge-{pr_id}-{active_run_id}"
    
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)

    # 1. Clean up stale state if it exists
    if path.exists():
        run_command(["git", "worktree", "remove", "--force", str(path)], cwd=repo_root, timeout_seconds=timeout_seconds)
    
    # Check for branch existence and delete it
    run_command(["git", "branch", "-D", branch], cwd=repo_root, timeout_seconds=timeout_seconds)

    # 2. Fetch the PR head into the dedicated branch
    fetch = run_command(
        ["git", "fetch", "origin", f"pull/{pr_id}/head:{branch}"],
        cwd=repo_root,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return None, None, fetch.stderr.strip() or "git fetch failed"
        
    # 3. Create the worktree
    add = run_command(
        ["git", "worktree", "add", str(path), branch],
        cwd=repo_root,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, add)
    if add.returncode != 0:
        return None, None, add.stderr.strip() or "git worktree add failed"
        
    return path, branch, None


def cleanup_worktree(
    repo_root: Path,
    worktree_path: Path,
    branch: str,
    commands_log: Path,
    policy: Dict[str, Any],
) -> None:
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    
    if worktree_path and worktree_path.exists():
        remove = run_command(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=repo_root,
            timeout_seconds=timeout_seconds,
        )
        append_command_log(commands_log, remove)
        
    if branch:
        run_command(
            ["git", "branch", "-D", branch],
            cwd=repo_root,
            timeout_seconds=timeout_seconds,
        )


def ensure_worktree_matches_pr_head(
    *,
    worktree_path: Path,
    pr_id: int,
    head_ref: str,
    client: GitHubClient,
    commands_log: Path,
    policy: Dict[str, Any],
) -> Tuple[bool, str]:
    expected_oid, err = client.fetch_pr_head_oid(pr_id)
    if err:
        return False, err
        
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    
    local_head = run_command(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree_path,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, local_head)
    if local_head.returncode != 0:
        return False, local_head.stderr.strip() or "Unable to read local worktree HEAD"
        
    if local_head.stdout.strip() == expected_oid:
        return True, "worktree already matched live PR head"
        
    fetch = run_command(
        ["git", "fetch", "origin", head_ref],
        cwd=worktree_path,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return False, fetch.stderr.strip() or "Unable to fetch live PR head"
        
    reset = run_command(
        ["git", "reset", "--hard", expected_oid],
        cwd=worktree_path,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, reset)
    if reset.returncode != 0:
        return (
            False,
            reset.stderr.strip() or "Unable to refresh worktree to live PR head",
        )
    return True, f"refreshed stale worktree to live PR head {expected_oid}"


def attempt_rebase(
    *,
    pr_id: int,
    worktree_path: Path,
    base_ref: str,
    head_ref: str,
    commands_log: Path,
    execute: bool,
    repo: Optional[str],
    policy: Dict[str, Any],
) -> Tuple[bool, bool, str]:
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    
    # Enable rerere for this worktree
    run_command(["git", "config", "rerere.enabled", "true"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    run_command(["git", "config", "rerere.autoupdate", "true"], cwd=worktree_path, timeout_seconds=timeout_seconds)

    command = ["gh", "pr", "update-branch", str(pr_id), "--rebase"]
    if repo:
        command.extend(["--repo", repo])
        
    update = execute_or_dry_run(
        command,
        execute=execute,
        cwd=worktree_path,
        commands_log=commands_log,
        timeout_seconds=timeout_seconds,
    )
    
    if execute and update.returncode != 0:
        if "conflict" in update.stderr.lower():
            fetch_base = run_command(
                ["git", "fetch", "origin", base_ref],
                cwd=worktree_path,
                timeout_seconds=timeout_seconds,
            )
            append_command_log(commands_log, fetch_base)
            local_rebase = run_command(
                ["git", "rebase", f"origin/{base_ref}"],
                cwd=worktree_path,
                timeout_seconds=timeout_seconds,
            )
            append_command_log(commands_log, local_rebase)
            detail = local_rebase.stderr.strip() or local_rebase.stdout.strip()
            return (
                False,
                True,
                update.stderr.strip()
                + (f"\n\nLocal conflict reproduction:\n{detail}" if detail else ""),
            )
        return False, False, update.stderr.strip() or "gh pr update-branch failed"
        
    if not execute:
        return True, False, "dry-run"
        
    fetch = run_command(
        ["git", "fetch", "origin", head_ref],
        cwd=worktree_path,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return False, False, fetch.stderr.strip() or "git fetch for head failed"
        
    reset = run_command(
        ["git", "reset", "--hard", f"origin/{head_ref}"],
        cwd=worktree_path,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, reset)
    if reset.returncode != 0:
        return False, False, reset.stderr.strip() or "git reset to rebased head failed"
        
    return True, False, "rebase updated and worktree refreshed"
