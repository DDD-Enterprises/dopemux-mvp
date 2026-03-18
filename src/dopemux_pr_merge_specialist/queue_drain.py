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
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Callable

from .github_api import BOT_AUTHORS, GitHubClient, ci_status, summarize_checks, thread_counters
from .policy import PolicyError, load_effective_policy, policy_artifact_payload, policy_fingerprint
from .runtime import CommandResult, append_command_log, execute_or_dry_run, fingerprint_payload, pid_is_running, run_command, run_id, shell_join, snapshot_environment, utc_now, write_json, write_text
from .schema import ARTIFACT_VERSION, ArtifactMeta, BlockerType, FallbackReason, Finding, FindingSeverity, Fingerprint, MergeDecision, MergeActionType, OverrideRecord, PhaseRecord, PRResult, PRState, PRStateData, POLICY_SCHEMA_VERSION, PreflightCheck, PreflightResult, PullRequestState, QueueOrderingLayer, ReviewThread, RunManifest, ThreadComment, ThreadDisposition, ThreadDispositionType, TruthSource, ValidationReport, ValidationStatus, TOOL_VERSION
from .validation import run_validation, validation_report_md
from .strategy_library import STRATEGY_LIBRARY



from .preflight import preflight, manifest_for_run, write_manifest, build_run_paths, pr_dir_for
from .plan_builder import artifact_meta, decision_basis_payload, plan_fingerprint, findings_from_pr_state, truth_sources_for, summarize_findings, explain_findings, build_plan_result, render_operator_summary, write_pr_state_artifact, _inflate_pr_result
from .classification import _status_value, _severity_value, _state_value, ensure_transition, classify_pr, risk_score, build_pr_state, lifecycle_for_findings, has_conflicts, CLASS_PRIORITY, VALID_TRANSITIONS, TRUTH_PRECEDENCE
from .queue import parse_pr_id_args, priority_key, build_dependency_edges, sort_states, apply_priority_preferences, snapshot_payload, require_clean_worktree, acquire_queue_lock, release_queue_lock, QUEUE_LOCK_PATH
from .thread_resolution import (
    latest_comment,
    contains_marker,
    has_newer_objection,
    has_resolution_signal,
    is_implementable_comment,
    decide_thread_disposition,
    graphql_escape,
    graph_reply_to_thread,
    graph_resolve_thread,
    _graphql_mutation_ok,
    _is_rate_limited,
    _execute_thread_graphql,
    apply_thread_dispositions,
)
from .conflict import (
    read_file_at_ref,
    maybe_sync_canonical_file,
    resolve_conflict_markers,
    apply_suggestion_to_file,
    comment_prefers_conflict_side,
    extract_suggestion_block,
    conflict_files,
    pr_changed_files,
    scan_files_for_conflict_markers,
    conflict_excerpt,
    recent_file_history,
    build_conflict_analysis,
    recommend_conflict_strategy,
)
from .merge import checks_green, wait_for_green_checks, checks_blocker_reason, decide_merge_action, run_merge_with_fallback, serialize_check_payload
from .worktree import prepare_worktree, cleanup_worktree, ensure_worktree_matches_pr_head, attempt_rebase

__all__ = ['queue_scan', 'queue_scan_internal', 'pr_plan', 'pr_apply', 'pr_merge', 'pr_approve', 'pr_ready', '_get_ops_engine', '_derive_allowed_actions', 'queue_drain', 'stage_and_push_if_needed', 'update_remaining_pr_bases']

def stage_and_push_if_needed(*, worktree_path: Path, head_ref: str, active_run_id: str, pr_id: int, execute: bool, commands_log: Path, policy: Dict[str, Any]) -> bool:
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    status = execute_or_dry_run(["git", "status", "--porcelain"], execute=execute, cwd=worktree_path, commands_log=commands_log, timeout_seconds=timeout_seconds)
    if not execute:
        return bool(status.stdout.strip())
    if status.returncode != 0 or not status.stdout.strip():
        return False
    add = run_command(["git", "add", "-A"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    append_command_log(commands_log, add)
    if add.returncode != 0:
        return False
    commit = run_command(["git", "commit", "-m", f"review-response: address thread suggestions (pr-merge/{active_run_id}/PR-{pr_id})"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    append_command_log(commands_log, commit)
    if commit.returncode != 0:
        return False
    push = run_command(["git", "push", "origin", f"HEAD:{head_ref}", "--force-with-lease"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    append_command_log(commands_log, push)
    return push.returncode == 0

def update_remaining_pr_bases(*, remaining: Iterable[int], execute: bool, repo: Optional[str], commands_log: Path, repo_root: Path, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    updates: List[Dict[str, Any]] = []
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    for pr_id in remaining:
        command = ["gh", "pr", "update-branch", str(pr_id), "--rebase"]
        if repo:
            command.extend(["--repo", repo])
        result = execute_or_dry_run(command, execute=execute, cwd=repo_root, commands_log=commands_log, timeout_seconds=timeout_seconds)
        updates.append({"pr_id": pr_id, "command": command, "returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    return updates

def queue_scan_internal(args: argparse.Namespace, client: GitHubClient, policy: Dict[str, Any], active_run_id: str) -> List[PRResult]:
    repo_root = Path.cwd()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    repo_slug = client.resolve_repo_slug()
    
    raws = client.fetch_open_prs(int(args.limit))
    states: List[PullRequestState] = []
    results: List[PRResult] = []
    for raw in raws:
        threads = client.fetch_review_threads(int(raw["number"]))
        unresolved_total, active_threads, outdated_threads = thread_counters(threads)
        pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
        check_payload = client.query_checks(pr.pr_id)
        validation = ValidationReport(
            status=ValidationStatus.NOT_EXECUTED,
            required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
            steps=[],
            attempts=0,
            remediation_applied=False,
        )
        results.append(build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy))
        states.append(pr)
    
    # Apply ordering logic
    ordered, layers, edges, cycle = sort_states(
        apply_priority_preferences(
            states, 
            only_ids=parse_pr_id_args(getattr(args, "only", []) or []), 
            prioritize_ids=parse_pr_id_args(getattr(args, "prioritize", []) or [])
        ), 
        args.strategy,
        policy=policy
    )
    ordered_ids = [state.pr_id for state in ordered]
    
    # Filter results based on ordering if needed, or just return results in priority order
    priority_map = {pr.pr_id: i for i, pr in enumerate(ordered)}
    results.sort(key=lambda r: priority_map.get(r.pr_state.pr_id, 999999))
    
    # Snapshot for persistence
    write_json(queue_dir / "QUEUE_SNAPSHOT.json", {
        "meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(),
        "states": snapshot_payload(states),
        "cache": client.cache_summary()
    })
    write_json(queue_dir / "ORDERING_PLAN.json", {
        "meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(),
        "strategy": args.strategy,
        "cycle_detected": cycle,
        "layers": [layer.to_dict() for layer in layers],
        "edges": edges,
        "ordered_pr_ids": ordered_ids
    })
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    
    return results

def queue_scan(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    
    manifest = manifest_for_run(active_run_id=active_run_id, mode="queue-scan", repo_root=repo_root, repo_slug=repo_slug, policy=policy)
    
    results = queue_scan_internal(args, client, policy, active_run_id)
    
    manifest.completed_phases.append("queue-scan")
    manifest.artifact_pointers.update({
        "queue_snapshot": str(queue_dir / "QUEUE_SNAPSHOT.json"),
        "ordering_plan": str(queue_dir / "ORDERING_PLAN.json")
    })
    write_manifest(run_dir, manifest)
    write_text(run_dir / "RUN_SUMMARY.md", render_operator_summary(results))
    
    print(f"Open PRs: {len(results)}")
    print(f"Artifacts: {run_dir}")
    return 0

def pr_plan(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    raw = client.fetch_pr(int(args.id))
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    check_payload = client.query_checks(pr.pr_id)
    validation = ValidationReport(
        status=ValidationStatus.NOT_EXECUTED,
        required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
        steps=[],
        attempts=0,
        remediation_applied=False,
    )
    result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy)
    explain = json.loads(result.artifacts["explain"])
    write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
    write_json(pr_dir / "REVIEW_THREADS.json", {"threads": [thread.to_dict() for thread in threads]})
    write_json(pr_dir / "PLAN.json", result.to_dict())
    write_json(pr_dir / "EXPLAIN.json", explain)
    write_pr_state_artifact(pr_dir, result)
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    print(f"Plan artifacts: {pr_dir}")
    return 0

def remediate_ci_failure(worktree_path: Path, validation_report: ValidationReport, log: Callable, timeout_seconds: int = 120) -> bool:
    failed_steps = [s for s in validation_report.steps if s.status == "failed"]
    if not failed_steps:
        return False
        
    step = failed_steps[0]
    log(f"Analyzing CI failure from step '{step.name}'...")
    
    error_output = (step.stderr or step.stdout or "No output available")[-4000:]
    
    prompt = f"""
You are an expert developer fixing a CI failure. 
The following command failed: {step.command}

Output/Error:
```
{error_output}
```

Identify the files to fix, and output ONLY valid bash commands to apply the fix (e.g., using sed, perl, python -c, or echo) in the current directory.
DO NOT include any markdown formatting, explanations, or backticks around the script. Output the raw bash script.
"""
    
    log("Calling AI to synthesize a fix...")
    
    import subprocess
    try:
        process = subprocess.Popen(
            ["gemini", "chat", "--system", prompt],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=worktree_path,
        )
        stdout, stderr = process.communicate(input="Please generate the bash script to fix this.", timeout=timeout_seconds)
    except Exception as e:
        log(f"AI invocation failed: {e}", "ERROR")
        return False
        
    if process.returncode != 0:
        log("AI failed to generate a fix.", "ERROR")
        return False
        
    fix_script = stdout.strip()
    if not fix_script:
        log("AI returned an empty fix.", "ERROR")
        return False
        
    # Remove markdown code blocks if AI included them despite instructions
    fix_script = re.sub(r"^```(bash|sh)?\n?", "", fix_script, flags=re.IGNORECASE)
    fix_script = re.sub(r"\n?```$", "", fix_script)
    fix_script = fix_script.strip()
    
    log("Applying synthesized fix...")
    
    fix_path = worktree_path / ".dopemux_ci_fix.sh"
    fix_path.write_text(fix_script)
    fix_path.chmod(0o755)
    
    try:
        apply_result = subprocess.run(
            [str(fix_path)],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except Exception as e:
        log(f"Fix application failed: {e}", "ERROR")
        return False
        
    if apply_result.returncode != 0:
        log("Synthesized fix failed to resolve the issue.", "ERROR")
        return False
        
    log("AI fix applied successfully.", "SUCCESS")
    return True

def pr_apply(args: argparse.Namespace, progress_callback: Optional[Callable[[str, str], None]] = None) -> PRResult:
    def log(msg: str, s_type: str = "INFO"):
        if progress_callback:
            progress_callback(msg, s_type)
            
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    
    log(f"Fetching PR #{args.id} subspace data...")
    raw = client.fetch_pr(int(args.id))
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    commands_log = pr_dir / "COMMANDS_RUN.txt"
    write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
    
    worktree_path: Optional[Path] = None
    branch: Optional[str] = None
    blockers: List[Finding] = []
    thread_dispositions = [decide_thread_disposition(thread, validation_green=pr.ci_status == "SUCCESS", policy=policy) for thread in threads if not thread.is_resolved]
    
    execute = getattr(args, "execute", False)
    lock_path: Optional[Path] = None
    if execute:
        ok, lock_path, err = acquire_queue_lock(repo_root=repo_root, active_run_id=active_run_id)
        if not ok:
            raise RuntimeError(f"Unable to acquire queue lock: {err}")
            
    try:
        log("Initializing isolated worktree...")
        worktree_path, branch, err = prepare_worktree(repo_root=repo_root, pr_id=pr.pr_id, active_run_id=active_run_id, commands_log=commands_log, policy=policy)
        if err:
            raise RuntimeError(f"Error preparing worktree: {err}")
            
        log("Checking worktree head OID...")
        matches, err = ensure_worktree_matches_pr_head(worktree_path=worktree_path, pr_id=pr.pr_id, head_ref=pr.head_ref, client=client, commands_log=commands_log, policy=policy)
        if not matches:
            raise RuntimeError(f"Worktree head mismatch: {err}")
            
        log(f"Attempting rebase on {pr.base_ref}...")
        rebase_ok, rebase_diverged, rebase_error = attempt_rebase(pr_id=pr.pr_id, worktree_path=worktree_path, base_ref=pr.base_ref, head_ref=pr.head_ref, commands_log=commands_log, execute=execute, repo=getattr(args, "repo", None), policy=policy)
        if not rebase_ok:
            blockers.append(Finding(id="rebase_conflict", severity=FindingSeverity.BLOCKER, category="conflict", message=f"Rebase failed on {pr.base_ref}", details={"error": rebase_error}, suggestion="Manual resolution required."))
            
        log("Applying thread dispositions...")
        threads_by_id = {thread.id: thread for thread in threads}
        applied_threads = apply_thread_dispositions(
            dispositions=thread_dispositions,
            threads_by_id=threads_by_id,
            worktree_path=worktree_path,
            base_ref=pr.base_ref,
            execute=execute,
            commands_log=commands_log,
            repo_root=repo_root,
            policy=policy
        )
        if any(d.disposition == ThreadDispositionType.IMPLEMENT for d in applied_threads):
            log("Pushing implemented suggestions...")
            stage_and_push_if_needed(worktree_path=worktree_path, head_ref=pr.head_ref, active_run_id=active_run_id, pr_id=pr.pr_id, execute=execute, commands_log=commands_log, policy=policy)
            
        log("Running validation suite...", "START")
        validation = run_validation(
            repo_root=repo_root,
            worktree_path=worktree_path,
            policy=policy,
            execute=execute,
            commands_log=commands_log,
            pr_id=pr.pr_id,
            head_sha=pr.head_sha,
            base_sha=pr.base_sha,
            policy_fingerprint=policy_fingerprint(policy),
            lifecycle_state=(
                pr.lifecycle_state.value
                if hasattr(pr.lifecycle_state, "value")
                else str(pr.lifecycle_state)
            ),
            progress_callback=progress_callback
        )
        
        if not validation.passed and execute:
            log("Validation failed, attempting AI remediation...")
            if remediate_ci_failure(worktree_path, validation, log):
                log("Re-running validation suite after AI fix...", "START")
                validation = run_validation(
                    repo_root=repo_root,
                    worktree_path=worktree_path,
                    policy=policy,
                    execute=execute,
                    commands_log=commands_log,
                    pr_id=pr.pr_id,
                    head_sha=pr.head_sha,
                    base_sha=pr.base_sha,
                    policy_fingerprint=policy_fingerprint(policy),
                    lifecycle_state=(
                        pr.lifecycle_state.value
                        if hasattr(pr.lifecycle_state, "value")
                        else str(pr.lifecycle_state)
                    ),
                    progress_callback=progress_callback
                )
                if validation.passed:
                    log("Committing AI remediation fix...")
                    stage_and_push_if_needed(worktree_path=worktree_path, head_ref=pr.head_ref, active_run_id=active_run_id, pr_id=pr.pr_id, execute=execute, commands_log=commands_log, policy=policy)
        
        if validation.passed:
            log("Validation PASSED", "SUCCESS")
        else:
            log("Validation FAILED", "ERROR")
            
        result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=client.query_checks(pr.pr_id), validation_report=validation, policy=policy)
        write_pr_state_artifact(pr_dir, result)
        return result
    finally:
        if execute:
            log("Cleaning up worktree...")
            if worktree_path and branch:
                cleanup_worktree(repo_root=repo_root, worktree_path=worktree_path, branch=branch, commands_log=commands_log, policy=policy)
            release_queue_lock(lock_path)

def pr_merge(args: argparse.Namespace, progress_callback: Optional[Callable[[str, str], None]] = None) -> PRResult:
    def log(msg: str, s_type: str = "INFO"):
        if progress_callback:
            progress_callback(msg, s_type)
            
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    
    log(f"Fetching final state for PR #{args.id}...")
    raw = client.fetch_pr(int(args.id))
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    check_payload = client.query_checks(pr.pr_id)
    
    validation = ValidationReport(status=ValidationStatus.NOT_EXECUTED, required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)), steps=[], attempts=0, remediation_applied=False)
    
    execute = getattr(args, "execute", False)
    if execute:
        log("Executing merge command...")
        merge_ok, merge_error = run_merge_with_fallback(client=client, pr_id=pr.pr_id, execute=execute, policy=policy)
        if not merge_ok:
            log(f"Merge FAILED: {merge_error}", "ERROR")
            raise RuntimeError(f"Merge failed: {merge_error}")
        log("Merge successful", "SUCCESS")
        
    result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy)
    write_pr_state_artifact(pr_dir, result)
    return result

def pr_approve(args: argparse.Namespace, progress_callback: Optional[Callable[[str, str], None]] = None) -> PRResult:
    def log(msg: str, s_type: str = "INFO"):
        if progress_callback:
            progress_callback(msg, s_type)
            
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    
    raw = client.fetch_pr(int(args.id))
    author = (raw.get("author") or {}).get("login", "unknown")
    auth_user = client.get_authenticated_user()
    
    log(f"Approving PR #{args.id}...")
    
    execute = getattr(args, "execute", False)
    if execute:
        if author == auth_user:
            log(f"Skipping approval: {auth_user} is the PR author.", "WARNING")
        else:
            cmd = ["gh", "pr", "review", str(args.id), "--approve"]
            if getattr(args, "repo", None):
                cmd.extend(["--repo", args.repo])
                
            result = run_command(cmd, cwd=repo_root, timeout_seconds=30)
            if result.returncode == 0:
                log("PR approved successfully.", "SUCCESS")
            else:
                log(f"Approval FAILED: {result.stderr.strip()}", "ERROR")
                raise RuntimeError(f"Approval failed: {result.stderr.strip()}")
            
    # Refresh state
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    check_payload = client.query_checks(pr.pr_id)
    validation = ValidationReport(status=ValidationStatus.NOT_EXECUTED, required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)), steps=[], attempts=0, remediation_applied=False)
    result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy)
    write_pr_state_artifact(pr_dir, result)
    return result

def pr_ready(args: argparse.Namespace, progress_callback: Optional[Callable[[str, str], None]] = None) -> PRResult:
    def log(msg: str, s_type: str = "INFO"):
        if progress_callback:
            progress_callback(msg, s_type)
            
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    
    log(f"Marking PR #{args.id} as READY...")
    
    execute = getattr(args, "execute", False)
    if execute:
        if client.ready_pr(int(args.id)):
            log("PR marked as READY.", "SUCCESS")
        else:
            log("Failed to mark PR as READY.", "ERROR")
            raise RuntimeError("gh pr ready failed")
            
    # Refresh state
    raw = client.fetch_pr(int(args.id))
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    check_payload = client.query_checks(pr.pr_id)
    validation = ValidationReport(status=ValidationStatus.NOT_EXECUTED, required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)), steps=[], attempts=0, remediation_applied=False)
    result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy)
    write_pr_state_artifact(pr_dir, result)
    return result

def _get_ops_engine(out_dir: Path) -> FlightDeckOpsEngine:
    from .ops_engine import FlightDeckOpsEngine
    ops_dir = out_dir / "ops"
    ops_dir.mkdir(parents=True, exist_ok=True)
    return FlightDeckOpsEngine(ops_dir)

def _derive_allowed_actions(result: PRResult, policy: Dict[str, Any]) -> List[str]:
    actions = []
    if result.lifecycle_state == "READY_FOR_MERGE":
        actions.append("MERGE")
    if result.lifecycle_state in ["BLOCKED_BY_THREADS", "CONFLICTED"]:
        actions.append("APPLY_FIX")
    return actions

def queue_drain(args: argparse.Namespace) -> int:
    from .closed_loop_engine import ClosedLoopEngine
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    ops = _get_ops_engine(run_dir)
    closed_loop = ClosedLoopEngine(ops, STRATEGY_LIBRARY)
    
    execute = getattr(args, "execute", False)
    lock_path: Optional[Path] = None
    if execute:
        ok, lock_path, err = acquire_queue_lock(repo_root=repo_root, active_run_id=active_run_id)
        if not ok:
            print(f"Error: {err}")
            return 1
            
    try:
        max_passes = int(getattr(args, "max_passes", 3))
        processed_ids = set()
        merged_ids = set()
        for pass_idx in range(max_passes):
            print(f"\n--- Queue Pass {pass_idx + 1}/{max_passes} ---")
            results = queue_scan_internal(args, client, policy, active_run_id)
            if not results:
                print("No PRs found.")
                break
            active_results = [r for r in results if r.pr_state.pr_id not in merged_ids]
            if not active_results:
                print("All PRs processed or merged.")
                break
            for result in active_results:
                pr_id = result.pr_state.pr_id
                processed_ids.add(pr_id)
                allowed = _derive_allowed_actions(result, policy)
                report = result.to_dict()
                report["allowed_actions"] = allowed
                trace = closed_loop.run_cycle(str(pr_id), report)
                closed_loop.emit_trace_artifacts(trace, pr_dir_for(pr_root, pr_id) / "traces")
                tactic = trace.next_tactic
                print(f"PR #{pr_id}: {result.lifecycle_state} -> Tactic: {tactic}")
                if tactic == "MERGE" and execute:
                    try:
                        if pr_merge(argparse.Namespace(**{**vars(args), "id": pr_id})) == 0:
                            merged_ids.add(pr_id)
                    except RuntimeError as e:
                        print(f"Merge error for PR #{pr_id}: {e}")
                elif tactic == "APPLY_FIX" and execute:
                    try:
                        pr_apply(argparse.Namespace(**{**vars(args), "id": pr_id}))
                    except RuntimeError as e:
                        print(f"Apply error for PR #{pr_id}: {e}")
        print(f"\nRun ID: {active_run_id}")
        print(f"Processed PRs: {len(processed_ids)}")
        print(f"Merged: {len(merged_ids)}")
        print(f"Artifacts: {run_dir}")
        return 0
    finally:
        if execute:
            release_queue_lock(lock_path)
