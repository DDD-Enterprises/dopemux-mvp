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
from .conflict import (
    conflict_files,
    conflict_recovery_policy,
    resolve_conflict_markers,
    safe_conflict_surface,
    scan_files_for_conflict_markers,
)
from .conflicts import ConflictAnalyzer
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
    "push_rebased_head",
    "auto_recover_rebase_conflicts",
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
            if local_rebase.returncode == 0:
                return (
                    True,
                    True,
                    "local rebase succeeded after GitHub reported conflicts",
                )
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


def attempt_speculative_rebase(
    *,
    worktree_path: Path,
    onto_ref: str,
    commands_log: Path,
    execute: bool,
    policy: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Perform a local rebase of the current HEAD onto an arbitrary onto_ref.
    Used for speculative 'Train' rebasing.
    """
    if not execute:
        return True, "dry-run"

    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    
    # Enable rerere
    run_command(["git", "config", "rerere.enabled", "true"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    run_command(["git", "config", "rerere.autoupdate", "true"], cwd=worktree_path, timeout_seconds=timeout_seconds)

    rebase = run_command(
        ["git", "rebase", onto_ref],
        cwd=worktree_path,
        timeout_seconds=timeout_seconds,
    )
    append_command_log(commands_log, rebase)
    
    if rebase.returncode == 0:
        return True, "speculative rebase succeeded"
    
    # Rebase failed (conflict). Abort.
    run_command(["git", "rebase", "--abort"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    return False, rebase.stderr.strip() or "speculative rebase failed with conflicts"


def push_rebased_head(
    *,
    worktree_path: Path,
    head_ref: str,
    commands_log: Path,
    execute: bool,
    policy: Dict[str, Any],
) -> Tuple[bool, str]:
    timeout_seconds = int(
        policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
    )
    push = execute_or_dry_run(
        ["git", "push", "origin", f"HEAD:{head_ref}", "--force-with-lease"],
        execute=execute,
        cwd=worktree_path,
        commands_log=commands_log,
        timeout_seconds=timeout_seconds,
    )
    if push.returncode != 0:
        return False, push.stderr.strip() or "git push of recovered head failed"
    return True, "rebased head pushed to PR branch"


def auto_recover_rebase_conflicts(
    *,
    pr: PullRequestState,
    worktree_path: Path,
    head_ref: str,
    rebase_error: str,
    commands_log: Path,
    execute: bool,
    policy: Dict[str, Any],
) -> Tuple[bool, str, Dict[str, Any]]:
    config = conflict_recovery_policy(policy)
    analyzer = ConflictAnalyzer()
    conflict_class = analyzer.classify_conflict(pr)
    telemetry: Dict[str, Any] = {
        "conflict_class": conflict_class.name,
        "rebase_error": rebase_error,
    }
    if not analyzer.is_auto_resolvable(conflict_class):
        return False, "semantic_conflict_blocked", telemetry

    timeout_seconds = int(
        policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
    )
    max_iterations = max(config["max_conflict_files"], 1) + 2
    for _ in range(max_iterations):
        files = conflict_files(worktree_path, policy)
        telemetry["conflict_files"] = files
        if not files:
            push_ok, push_message = push_rebased_head(
                worktree_path=worktree_path,
                head_ref=head_ref,
                commands_log=commands_log,
                execute=execute,
                policy=policy,
            )
            telemetry["push_message"] = push_message
            return push_ok, (
                "dirty_auto_recovered" if push_ok else "manual_conflict_required"
            ), telemetry
        if len(files) > config["max_conflict_files"]:
            telemetry["reason"] = "conflict_surface_too_large"
            return False, "manual_conflict_required", telemetry
        safe_surface, unsafe_files = safe_conflict_surface(files, policy)
        if not safe_surface:
            telemetry["unsafe_files"] = unsafe_files
            return False, "manual_conflict_required", telemetry
        marker_files = scan_files_for_conflict_markers(worktree_path, files)
        if sorted(marker_files) != sorted(files):
            telemetry["marker_files"] = marker_files
            return False, "manual_conflict_required", telemetry
        for rel_path in marker_files:
            file_path = worktree_path / rel_path
            text = file_path.read_text(encoding="utf-8")
            changed, resolved = resolve_conflict_markers(
                text, prefer=config["prefer_side"]
            )
            if not changed:
                telemetry["reason"] = resolved
                telemetry["failed_file"] = rel_path
                return False, "manual_conflict_required", telemetry
            file_path.write_text(resolved, encoding="utf-8")
        add = run_command(
            ["git", "add", *files],
            cwd=worktree_path,
            timeout_seconds=timeout_seconds,
        )
        append_command_log(commands_log, add)
        if add.returncode != 0:
            telemetry["reason"] = add.stderr.strip() or "git add failed"
            return False, "manual_conflict_required", telemetry
        cont = run_command(
            ["git", "rebase", "--continue"],
            cwd=worktree_path,
            env={"GIT_EDITOR": "true"},
            timeout_seconds=timeout_seconds,
        )
        append_command_log(commands_log, cont)
        if cont.returncode == 0:
            continue
        current_files = conflict_files(worktree_path, policy)
        if current_files:
            continue
        telemetry["reason"] = cont.stderr.strip() or cont.stdout.strip() or "git rebase --continue failed"
        return False, "manual_conflict_required", telemetry
    telemetry["reason"] = "recovery_iteration_limit_exceeded"
    return False, "manual_conflict_required", telemetry
