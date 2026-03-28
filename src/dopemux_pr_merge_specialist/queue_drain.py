from __future__ import annotations

import argparse
import html
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from collections import defaultdict, deque
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Callable

from .action_model import allowed_actions_for_result
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
    resolve_verified_threads,
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
    conflict_recovery_state,
)
from .merge import checks_green, wait_for_green_checks, checks_blocker_reason, decide_merge_action, run_merge_with_fallback, serialize_check_payload
from .worktree import prepare_worktree, cleanup_worktree, ensure_worktree_matches_pr_head, attempt_rebase, attempt_speculative_rebase, push_rebased_head, auto_recover_rebase_conflicts

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


def _load_pr_context(
    *, client: GitHubClient, pr_id: int, raw: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], List[ReviewThread], PullRequestState, Dict[str, Any]]:
    payload = dict(raw) if raw is not None else client.fetch_pr(pr_id)
    threads = client.fetch_review_threads(pr_id)
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(payload, unresolved_total, active_threads, outdated_threads)
    check_payload = client.query_checks(pr.pr_id, pr_payload=payload)
    return payload, threads, pr, check_payload


def _refresh_client_state(client: GitHubClient, pr_id: int) -> None:
    client.invalidate(f"pr:{pr_id}")
    client.invalidate(f"threads:{pr_id}")
    client.invalidate("open_prs:")


def _gemini_ci_remediation_command(prompt: str) -> List[str]:
    # Gemini CLI no longer accepts --skill in headless mode, so the runbook
    # must live in the prompt and the invocation stays prompt-only.
    return ["gemini", "--prompt", prompt, "--yolo"]


def _inflate_result_from_state_path(state_path: Path) -> Optional[PRResult]:
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return PRResult(**_inflate_pr_result(payload))
    except Exception:
        return None


def _validation_state_is_reusable(result: PRResult, pr: PullRequestState) -> bool:
    prior_pr = result.pr_state
    if prior_pr.pr_id != pr.pr_id:
        return False
    if not prior_pr.head_sha or prior_pr.head_sha != pr.head_sha:
        return False
    if not prior_pr.base_sha or prior_pr.base_sha != pr.base_sha:
        return False
    if result.validation_report is None:
        return False
    return (
        _status_value(result.validation_report.status)
        != ValidationStatus.NOT_EXECUTED.value
    )


def _reusable_prior_result(
    *, out_dir: str, active_run_id: str, pr: PullRequestState
) -> Optional[PRResult]:
    root = Path(out_dir)
    current_state = root / f"run_{active_run_id}" / "pr" / str(pr.pr_id) / "STATE.json"
    candidates: List[Path] = []
    if current_state.exists():
        candidates.append(current_state)
    historical = sorted(
        (
            path
            for path in root.glob(f"run_*/pr/{pr.pr_id}/STATE.json")
            if path != current_state
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    candidates.extend(historical)
    for state_path in candidates:
        prior_result = _inflate_result_from_state_path(state_path)
        if prior_result and _validation_state_is_reusable(prior_result, pr):
            return prior_result
    return None


def _threads_resolved_locally(result: Optional[PRResult]) -> bool:
    if result is None:
        return False
    return any(
        finding.finding_type == "threads_resolved_locally"
        for finding in result.findings
    )


def _with_operator_state(
    result: PRResult, operator_state: str, *, detail: str = ""
) -> PRResult:
    artifacts = dict(result.artifacts)
    artifacts["operator_state"] = operator_state
    if detail:
        artifacts["operator_state_detail"] = detail
    lifecycle_state = (
        PRState.QUEUED_FOR_MERGE.value
        if operator_state == "queued_for_merge"
        else result.lifecycle_state
    )
    return replace(result, lifecycle_state=lifecycle_state, artifacts=artifacts)


def _merge_prepared_result(
    *,
    args: argparse.Namespace,
    client: GitHubClient,
    repo_root: Path,
    policy: Dict[str, Any],
    pr_root: Path,
    active_run_id: str,
    prepared_result: PRResult,
    progress_callback: Optional[Callable[[str, str], None]] = None,
) -> PRResult:
    def log(msg: str, s_type: str = "INFO"):
        if progress_callback:
            progress_callback(msg, s_type)

    decision = prepared_result.merge_decision or MergeDecision(
        action=MergeActionType.BLOCKED,
        command=[],
        reason="Prepared result did not produce a merge decision.",
        reason_code="missing_merge_decision",
    )
    if _state_value(decision.action) == MergeActionType.BLOCKED.value:
        raise RuntimeError(decision.reason or "Merge blocked by current findings.")

    pr_id = prepared_result.pr_state.pr_id
    pr_dir = pr_dir_for(pr_root, pr_id)
    commands_log = pr_dir / "COMMANDS_RUN.txt"

    log("Executing merge command...")
    executed_decision = run_merge_with_fallback(
        decision=decision,
        pr_id=pr_id,
        execute=bool(getattr(args, "execute", False)),
        repo=getattr(args, "repo", None),
        commands_log=commands_log,
        repo_root=repo_root,
        policy=policy,
        client=client,
    )
    if _state_value(executed_decision.action) == MergeActionType.BLOCKED.value:
        raise RuntimeError(executed_decision.reason)

    _refresh_client_state(client, pr_id)
    raw, threads, pr, check_payload = _load_pr_context(client=client, pr_id=pr_id)
    
    # Check if prepared_result had locally resolved threads
    threads_resolved = any(
        f.finding_type == "threads_resolved_locally" 
        for f in getattr(prepared_result, "findings", [])
    )
    
    result = build_plan_result(
        active_run_id=active_run_id,
        pr=pr,
        threads=threads,
        check_payload=check_payload,
        validation_report=prepared_result.validation_report
        or ValidationReport(
            status=ValidationStatus.NOT_EXECUTED,
            required_for_merge_ready=bool(
                policy.get("validation", {}).get(
                    "require_local_validation_for_merge_ready", True
                )
            ),
            steps=[],
            attempts=0,
            remediation_applied=False,
        ),
        policy=policy,
        threads_resolved_locally=threads_resolved,
    )
    result = replace(result, merge_decision=executed_decision)
    write_pr_state_artifact(pr_dir, result)
    log("Merge successful", "SUCCESS")
    return result

def queue_scan_internal(args: argparse.Namespace, client: GitHubClient, policy: Dict[str, Any], active_run_id: str) -> List[PRResult]:
    repo_root = Path.cwd()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    repo_slug = client.resolve_repo_slug()
    
    raws = client.fetch_open_prs(int(args.limit))
    states: List[PullRequestState] = []
    results: List[PRResult] = []
    for raw in raws:
        _, threads, pr, check_payload = _load_pr_context(
            client=client, pr_id=int(raw["number"]), raw=raw
        )
        prior_result = _reusable_prior_result(
            out_dir=args.out_dir,
            active_run_id=active_run_id,
            pr=pr,
        )
        validation = (
            prior_result.validation_report
            if prior_result and prior_result.validation_report is not None
            else ValidationReport(
                status=ValidationStatus.NOT_EXECUTED,
                required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
                steps=[],
                attempts=0,
                remediation_applied=False,
            )
        )
        results.append(
            build_plan_result(
                active_run_id=active_run_id,
                pr=pr,
                threads=threads,
                check_payload=check_payload,
                validation_report=validation,
                policy=policy,
                previous_result=(
                    prior_result.to_dict() if prior_result is not None else None
                ),
                threads_resolved_locally=_threads_resolved_locally(prior_result),
            )
        )
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

    result_by_id = {item.pr_state.pr_id: item for item in results}
    results = [
        result_by_id[pr_id]
        for pr_id in ordered_ids
        if pr_id in result_by_id
    ]
    
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
    raw, threads, pr, check_payload = _load_pr_context(client=client, pr_id=int(args.id))
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
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

def remediate_ci_failure(worktree_path: Path, validation_report: ValidationReport, log: Callable, timeout_seconds: int = 300) -> bool:
    failed_steps = [s for s in validation_report.steps if s.status == "failed"]
    if not failed_steps:
        return False
        
    step = failed_steps[0]
    log(f"Engaging agentic remediation for step '{step.name}'...")
    
    error_output = (step.stderr or step.stdout or "No output available")[-6000:]
    
    prompt = f"""
You are an expert developer fixing a CI failure in the dopemux-mvp workspace.
The following command failed in this worktree: {step.command}

Output/Error:
```
{error_output}
```

Please diagnose the issue and FIX IT. You are running in YOLO mode with full tool access. 

CRITICAL: You MUST follow the ci-remediation-specialist runbook:
1. REPRODUCE the failure locally first by running the command `{step.command}`.
2. USE AUTO-FIXERS if applicable (e.g., ruff check --fix).
3. APPLY a minimal surgical fix if reproduction succeeds.
4. VERIFY that your fix makes `{step.command}` pass.

Identify the root cause, modify the necessary files, and ensure the command passes.
"""
    
    log(f"Launching Gemini CLI agent in YOLO mode (worktree: {worktree_path.name})...")
    
    try:
        cmd = _gemini_ci_remediation_command(prompt)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=worktree_path,
            bufsize=1, # Line buffered
            universal_newlines=True,
        )
        
        # Stream output to log in real-time
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                clean_line = line.strip()
                if clean_line:
                    log(f"[gemini] {clean_line}")
                    
                    # Proactive quota detection
                    lowered = clean_line.lower()
                    if any(x in lowered for x in ["quota", "rate limit", "429", "exhausted"]):
                        log("CRITICAL: API QUOTA EXHAUSTED. GEMINI REMEDIATION BLOCKED.", "ERROR")
                
        process.wait(timeout=timeout_seconds)
        
    except subprocess.TimeoutExpired:
        process.kill()
        log("Gemini agent timed out.", "ERROR")
        return False
    except Exception as e:
        log(f"Agentic remediation process crash: {e}", "ERROR")
        return False
        
    if process.returncode != 0:
        log(f"Agent finished with non-zero exit code ({process.returncode}).", "WARNING")
        return False
        
    log("Agentic remediation cycle complete.")
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
    raw, threads, pr, check_payload = _load_pr_context(client=client, pr_id=int(args.id))
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    commands_log = pr_dir / "COMMANDS_RUN.txt"
    write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
    
    worktree_path: Optional[Path] = None
    branch: Optional[str] = None
    thread_dispositions = [decide_thread_disposition(thread, validation_green=pr.ci_status == "SUCCESS", policy=policy) for thread in threads if not thread.is_resolved]
    
    execute = getattr(args, "execute", False)
    lock_path: Optional[Path] = None
    owns_lock = execute and not bool(getattr(args, "_queue_lock_held", False))
    if owns_lock:
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

        validation = ValidationReport(
            status=ValidationStatus.NOT_EXECUTED,
            required_for_merge_ready=bool(
                policy.get("validation", {}).get(
                    "require_local_validation_for_merge_ready", True
                )
            ),
            steps=[],
            attempts=0,
            remediation_applied=False,
        )
        operator_state = ""
        conflict_state = (
            conflict_recovery_state(pr, policy)
            if has_conflicts(pr.mergeable, pr.merge_state_status)
            else ""
        )
        if conflict_state in {"manual_conflict_required", "semantic_conflict_blocked"}:
            analysis_path = pr_dir / "CONFLICT_ANALYSIS.md"
            write_text(
                analysis_path,
                build_conflict_analysis(
                    pr=pr,
                    worktree_path=worktree_path,
                    rebase_error="Conflict automation declined before rebase because the PR is not opted in for mechanical recovery.",
                    policy=policy,
                ),
            )
            result = build_plan_result(
                active_run_id=active_run_id,
                pr=pr,
                threads=threads,
                check_payload=check_payload,
                validation_report=validation,
                policy=policy,
            )
            result = _with_operator_state(
                result,
                conflict_state,
                detail=str(analysis_path),
            )
            write_pr_state_artifact(pr_dir, result)
            return result

        # Phase 1: Apply Thread Suggestions (Resolved Comments)
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
            if stage_and_push_if_needed(worktree_path=worktree_path, head_ref=pr.head_ref, active_run_id=active_run_id, pr_id=pr.pr_id, execute=execute, commands_log=commands_log, policy=policy):
                _refresh_client_state(client, pr.pr_id)

        # Phase 2: Rebase on Base Branch
        log(f"Attempting rebase on {pr.base_ref}...")
        rebase_ok, rebase_diverged, rebase_error = attempt_rebase(pr_id=pr.pr_id, worktree_path=worktree_path, base_ref=pr.base_ref, head_ref=pr.head_ref, commands_log=commands_log, execute=execute, repo=getattr(args, "repo", None), policy=policy)
        if rebase_ok and rebase_diverged:
            log("Recovered via local rebase; pushing refreshed branch head...")
            push_ok, push_message = push_rebased_head(
                worktree_path=worktree_path,
                head_ref=pr.head_ref,
                commands_log=commands_log,
                execute=execute,
                policy=policy,
            )
            if not push_ok:
                raise RuntimeError(push_message)
            operator_state = "dirty_auto_recovered"
            _refresh_client_state(client, pr.pr_id)
        elif not rebase_ok:
            analysis_path = pr_dir / "CONFLICT_ANALYSIS.md"
            write_text(
                analysis_path,
                build_conflict_analysis(
                    pr=pr,
                    worktree_path=worktree_path,
                    rebase_error=rebase_error,
                    policy=policy,
                ),
            )
            if conflict_state == "eligible":
                log("Attempting automated mechanical conflict recovery...")
                recovered, recovery_state, _recovery_meta = auto_recover_rebase_conflicts(
                    pr=pr,
                    worktree_path=worktree_path,
                    head_ref=pr.head_ref,
                    rebase_error=rebase_error,
                    commands_log=commands_log,
                    execute=execute,
                    policy=policy,
                )
                if not recovered:
                    result = build_plan_result(
                        active_run_id=active_run_id,
                        pr=pr,
                        threads=threads,
                        check_payload=check_payload,
                        validation_report=validation,
                        policy=policy,
                    )
                    result = _with_operator_state(
                        result,
                        recovery_state,
                        detail=str(analysis_path),
                    )
                    write_pr_state_artifact(pr_dir, result)
                    return result
                operator_state = recovery_state
                _refresh_client_state(client, pr.pr_id)
            else:
                result = build_plan_result(
                    active_run_id=active_run_id,
                    pr=pr,
                    threads=threads,
                    check_payload=check_payload,
                    validation_report=validation,
                    policy=policy,
                )
                result = _with_operator_state(
                    result,
                    "manual_conflict_required",
                    detail=str(analysis_path),
                )
                write_pr_state_artifact(pr_dir, result)
                return result

        # Phase 3: Validation
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
                    if stage_and_push_if_needed(worktree_path=worktree_path, head_ref=pr.head_ref, active_run_id=active_run_id, pr_id=pr.pr_id, execute=execute, commands_log=commands_log, policy=policy):
                        _refresh_client_state(client, pr.pr_id)
        
        if validation.passed:
            log("Validation PASSED", "SUCCESS")
            # Resolve threads only after validation passes
            resolve_verified_threads(
                dispositions=applied_threads,
                execute=execute,
                commands_log=commands_log,
                repo_root=repo_root,
                policy=policy
            )
        else:
            log("Validation FAILED", "ERROR")
            
        _refresh_client_state(client, pr.pr_id)
        raw, threads, refreshed_pr, refreshed_checks = _load_pr_context(
            client=client, pr_id=pr.pr_id
        )
        result = build_plan_result(
            active_run_id=active_run_id,
            pr=refreshed_pr,
            threads=threads,
            check_payload=refreshed_checks,
            validation_report=validation,
            policy=policy,
            threads_resolved_locally=validation.passed and any(d.applied for d in applied_threads)
        )
        if operator_state:
            result = _with_operator_state(result, operator_state)
        write_pr_state_artifact(pr_dir, result)
        return result
    finally:
        if execute:
            log("Cleaning up worktree...")
            if worktree_path and branch:
                cleanup_worktree(repo_root=repo_root, worktree_path=worktree_path, branch=branch, commands_log=commands_log, policy=policy)
            if owns_lock:
                release_queue_lock(lock_path)

def pr_merge(args: argparse.Namespace, progress_callback: Optional[Callable[[str, str], None]] = None) -> PRResult:
    def log(msg: str, s_type: str = "INFO"):
        if progress_callback:
            progress_callback(msg, s_type)
            
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    _, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    execute = getattr(args, "execute", False)
    owns_lock = execute and not bool(getattr(args, "_queue_lock_held", False))
    lock_path: Optional[Path] = None
    if owns_lock:
        ok, lock_path, err = acquire_queue_lock(
            repo_root=repo_root, active_run_id=active_run_id
        )
        if not ok:
            raise RuntimeError(f"Unable to acquire queue lock: {err}")

    try:
        if execute:
            log(f"Preparing merge readiness for PR #{args.id}...")
            apply_args = argparse.Namespace(
                **{**vars(args), "_queue_lock_held": True}
            )
            prepared_result = pr_apply(apply_args, progress_callback=progress_callback)
            return _merge_prepared_result(
                args=args,
                client=client,
                repo_root=repo_root,
                policy=policy,
                pr_root=pr_root,
                active_run_id=active_run_id,
                prepared_result=prepared_result,
                progress_callback=progress_callback,
            )

        log(f"Fetching final state for PR #{args.id}...")
        raw, threads, pr, check_payload = _load_pr_context(
            client=client, pr_id=int(args.id)
        )
        pr_dir = pr_dir_for(pr_root, pr.pr_id)
        validation = ValidationReport(
            status=ValidationStatus.NOT_EXECUTED,
            required_for_merge_ready=bool(
                policy.get("validation", {}).get(
                    "require_local_validation_for_merge_ready", True
                )
            ),
            steps=[],
            attempts=0,
            remediation_applied=False,
        )
        result = build_plan_result(
            active_run_id=active_run_id,
            pr=pr,
            threads=threads,
            check_payload=check_payload,
            validation_report=validation,
            policy=policy,
        )
        write_pr_state_artifact(pr_dir, result)
        return result
    finally:
        if owns_lock:
            release_queue_lock(lock_path)

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
                _refresh_client_state(client, int(args.id))
            else:
                log(f"Approval FAILED: {result.stderr.strip()}", "ERROR")
                raise RuntimeError(f"Approval failed: {result.stderr.strip()}")
            
    # Refresh state
    raw, threads, pr, check_payload = _load_pr_context(client=client, pr_id=int(args.id))
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
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
            _refresh_client_state(client, int(args.id))
        else:
            log("Failed to mark PR as READY.", "ERROR")
            raise RuntimeError("gh pr ready failed")
            
    # Refresh state
    raw, threads, pr, check_payload = _load_pr_context(client=client, pr_id=int(args.id))
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
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
    return allowed_actions_for_result(result)

FINGERPRINT_MARKER = "<!-- bot:failure_fingerprint:"

def _parse_fingerprint_from_body(body: str) -> Optional[str]:
    """Extracts the failure fingerprint from a PR body."""
    if not body:
        return None
    for line in body.splitlines():
        if FINGERPRINT_MARKER in line:
            parts = line.split(FINGERPRINT_MARKER)
            if len(parts) > 1:
                return parts[1].split("-->")[0].strip()
    return None

def _create_global_fix_pr(fingerprint: str, failed_step: ValidationStepResult, client: GitHubClient, repo_root: Path) -> int:
    """Creates a global fix PR against the main branch."""
    import subprocess
    
    branch = f"global-ci-fix-{fingerprint[:8]}"
    path = Path("/tmp") / f"dopemux-global-fix-{fingerprint[:8]}"
    
    print(f"Creating global fix PR for fingerprint {fingerprint} on branch {branch}")
    
    # 1. Prepare worktree off main
    if path.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(path)], cwd=repo_root)
    subprocess.run(["git", "branch", "-D", branch], cwd=repo_root, stderr=subprocess.DEVNULL)
    
    # Fetch latest main
    subprocess.run(["git", "fetch", "origin", "main"], cwd=repo_root, check=True)
    subprocess.run(["git", "branch", branch, "origin/main"], cwd=repo_root, check=True)
    subprocess.run(["git", "worktree", "add", str(path), branch], cwd=repo_root, check=True)
    
    try:
        # 2. Invoke Gemini CLI to fix it
        error_output = (failed_step.stderr or failed_step.stdout or "No output available")[-6000:]
        prompt = f"""
You are an expert developer fixing a widespread CI failure in the dopemux-mvp workspace.
This failure is blocking multiple PRs.
The following command failed: {failed_step.command}

Output/Error:
```
{error_output}
```

Please diagnose the issue and FIX IT against the `main` branch. You are running in YOLO mode with full tool access. 
CRITICAL: You MUST follow the ci-remediation-specialist runbook:
1. REPRODUCE the failure locally first by running the command `{failed_step.command}`.
2. USE AUTO-FIXERS if applicable (e.g., ruff check --fix).
3. APPLY a minimal surgical fix if reproduction succeeds.
4. VERIFY that your fix makes `{failed_step.command}` pass.

Identify the root cause, modify the necessary files, and verify your fix if possible.
Your goal is to make the command `{failed_step.command}` pass.
"""
        print("Launching Gemini CLI agent for GLOBAL FIX...")
        cmd = _gemini_ci_remediation_command(prompt)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=path,
            bufsize=1,
            universal_newlines=True,
        )
        
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                clean_line = line.strip()
                if clean_line:
                    print(f"  [gemini-global-fix] {clean_line}")
                    if any(x in clean_line.lower() for x in ["quota", "rate limit", "429", "exhausted"]):
                        print("CRITICAL: API QUOTA EXHAUSTED. GLOBAL FIX BLOCKED.")
        process.wait()
        
        if process.returncode != 0:
            print("Global fix agent failed to complete successfully.")
            return -1
            
        # 3. Commit and push
        status = subprocess.run(["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True)
        if not status.stdout.strip():
            print("Global fix agent made no changes.")
            return -1
            
        subprocess.run(["git", "add", "-A"], cwd=path, check=True)
        subprocess.run(["git", "commit", "-m", f"fix: global CI remediation for {failed_step.name}\n\nAutomated fix generated by Dopemux."], cwd=path, check=True)
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=path, check=True)
        
        # 4. Create PR
        pr_body = (
            f"Automated CI fix for a recurring failure.\n\n"
            f"This PR was generated to address a widespread CI failure blocking the queue.\n\n"
            f"Failure Fingerprint: `{fingerprint}`\n\n"
            f"<!-- bot:failure_fingerprint:{fingerprint} -->"
        )
        
        create_cmd = [
            "gh", "pr", "create",
            "--title", f"fix: Global CI Remediation ({fingerprint[:8]})",
            "--body", pr_body,
            "--label", "global-ci-fix",
            "--head", branch,
            "--base", "main"
        ]
        if client.repo:
            create_cmd.extend(["--repo", client.repo])
            
        pr_result = subprocess.run(create_cmd, cwd=path, capture_output=True, text=True)
        if pr_result.returncode != 0:
            print(f"Failed to create PR: {pr_result.stderr}")
            return -1
            
        # Extract PR number from URL returned by gh pr create
        url = pr_result.stdout.strip()
        pr_num = int(url.split("/")[-1])
        print(f"Successfully created global fix PR #{pr_num}")
        return pr_num
        
    except Exception as e:
        print(f"Error creating global fix: {e}")
        return -1
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(path)], cwd=repo_root)

def _handle_global_ci_blockers(results: List[PRResult], client: GitHubClient, worktree_dir: Path):
    """
    Identifies PRs blocked by the same CI failure and manages global fix PRs.
    Modifies the 'results' list in-place.
    """
    # 1. Find existing global fix PRs and map them by fingerprint
    existing_fix_prs = client.find_global_fix_prs()
    fingerprint_to_pr_map: Dict[str, int] = {}
    for pr in existing_fix_prs:
        fingerprint = _parse_fingerprint_from_body(pr.get("body", ""))
        if fingerprint:
            fingerprint_to_pr_map[fingerprint] = pr["number"]

    # 2. Group failing PRs by their failure fingerprint
    failing_prs_by_fingerprint = defaultdict(list)
    for r in results:
        allowed = allowed_actions_for_result(r)
        if "APPLY_FIX" in allowed and r.validation_report and r.validation_report.failure_fingerprint:
            failing_prs_by_fingerprint[r.validation_report.failure_fingerprint].append(r)

    # 3. Process groups to identify and act on global blockers
    for fingerprint, blocked_prs in failing_prs_by_fingerprint.items():
        if len(blocked_prs) <= 1:
            continue  # Not a global blocker

        if fingerprint in fingerprint_to_pr_map:
            # A global fix PR already exists. Mark all grouped PRs as blocked.
            pr_number = fingerprint_to_pr_map[fingerprint]
            print(f"Found existing global fix PR #{pr_number} for fingerprint {fingerprint}")
            for r in blocked_prs:
                # We mutate the underlying data class instance here.
                # Since PRResult is frozen, we might need a workaround or update the list.
                # However, Python object mutation is complex for frozen dataclasses.
                # We'll use object.__setattr__ as a pragmatic workaround for this internal loop state.
                object.__setattr__(r, "blocked_by_global_fix_pr", pr_number)
        else:
            # New global blocker. Create a global fix PR.
            print(f"New global CI blocker detected for fingerprint: {fingerprint}. Triggering global fix.")
            failed_step = next(
                (
                    s
                    for s in blocked_prs[0].validation_report.steps
                    if s.status == "failed"
                ),
                None,
            )
            if failed_step:
                new_pr_number = _create_global_fix_pr(fingerprint, failed_step, client, worktree_dir)
                if new_pr_number > 0:
                    for r in blocked_prs:
                        object.__setattr__(r, "blocked_by_global_fix_pr", new_pr_number)
                else:
                    print(
                        f"Global fix creation failed for fingerprint {fingerprint}; "
                        "continuing with per-PR remediation."
                    )


def _ignite_speculative_train(
    results: List[PRResult], 
    client: GitHubClient, 
    repo_root: Path, 
    active_run_id: str,
    commands_log: Path,
    policy: Dict[str, Any],
    execute: bool
) -> Tuple[List[int], List[int]]:
    """
    Attempts to rebase a chain of READY PRs onto each other speculatively.
    Returns (merged_ids, queued_ids).
    """
    # 1. Identify READY PRs with green CI and no blockers
    # We only include PRs where the merge action would be REBASE_MERGE or AUTO_MERGE_FALLBACK
    train_candidates = [
        r for r in results 
        if r.lifecycle_state in (PRState.MERGE_READY.value, PRState.QUEUED_FOR_MERGE.value)
        and r.pr_state.ci_status == "SUCCESS"
        and r.pr_state.active_unresolved_threads == 0
    ]
    
    if len(train_candidates) < 2:
        return [], []

    print(f"\n🚂 IGNITING SPECULATIVE REBASE TRAIN ({len(train_candidates)} PRs)...")
    
    merged_ids = []
    queued_ids = []
    # Always rebase against the latest origin/main for the train
    # Speculative chaining (current_base = pr.head_ref) is risky with GitHub's native Merge Queue
    current_base = "origin/main"
    
    for i, result in enumerate(train_candidates):
        pr = result.pr_state
        print(f"  [Train {i+1}] Speculative Rebase for PR #{pr.pr_id}...")
        
        # Prepare worktree
        worktree_path, branch, err = prepare_worktree(repo_root, pr.pr_id, active_run_id, commands_log, policy)
        if err:
            print(f"    ❌ Worktree preparation failed: {err}")
            break
            
        try:
            # Rebase onto origin/main
            ok, msg = attempt_speculative_rebase(
                worktree_path=worktree_path,
                onto_ref=current_base,
                commands_log=commands_log,
                execute=execute,
                policy=policy
            )
            
            if not ok:
                print(f"    ❌ Speculative rebase failed: {msg}")
                continue # Skip this PR but try the next one in the train
                
            # Push rebased head
            if execute:
                push_ok, push_msg = push_rebased_head(
                    worktree_path=worktree_path,
                    head_ref=pr.head_ref,
                    commands_log=commands_log,
                    execute=True,
                    policy=policy
                )
                if not push_ok:
                    print(f"    ❌ Push failed: {push_msg}")
                    continue
                
                # Trigger merge --auto
                # If the repo uses Merge Queue, this will add it to the queue.
                merge_cmd = ["gh", "pr", "merge", str(pr.pr_id), "--auto", "--rebase", "--delete-branch"]
                if client.repo:
                    merge_cmd.extend(["--repo", client.repo])
                
                merge_res = execute_or_dry_run(merge_cmd, execute=True, cwd=repo_root, commands_log=commands_log)
                if merge_res.returncode == 0:
                    print(f"    ✅ Speculative rebase & auto-merge triggered.")
                    queued_ids.append(pr.pr_id)
                else:
                    print(f"    ⚠️ Auto-merge trigger failed: {merge_res.stderr}")
            else:
                print(f"    (Dry-run) Would rebase and trigger auto-merge.")
                queued_ids.append(pr.pr_id)
                
        finally:
            cleanup_worktree(repo_root, worktree_path, branch, commands_log, policy)
            
    return merged_ids, queued_ids


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
        max_prs = int(getattr(args, "max_prs", 0) or 0)
        processed_ids = set()
        merged_ids = set()
        queued_ids = set()
        failed_remediation_ids = set() # Track PRs that failed an attempt in THIS pass
        limit_reached = False
        
        for pass_idx in range(max_passes):
            print(f"\n--- Queue Pass {pass_idx + 1}/{max_passes} ---")
            results = queue_scan_internal(args, client, policy, active_run_id)
            if not results:
                print("No PRs found.")
                break
                
            _handle_global_ci_blockers(results, client, repo_root)
            
            # Ignite speculative rebase train for READY PRs
            pass_commands_log = run_dir / f"PASS_{pass_idx + 1}_TRAIN_COMMANDS.txt"
            train_merged, train_queued = _ignite_speculative_train(
                results, client, repo_root, active_run_id, pass_commands_log, policy, execute
            )
            merged_ids.update(train_merged)
            queued_ids.update(train_queued)
            for result in results:
                if result.lifecycle_state == PRState.MERGED.value:
                    merged_ids.add(result.pr_state.pr_id)
                elif (
                    result.lifecycle_state == PRState.QUEUED_FOR_MERGE.value
                    or str(result.artifacts.get("operator_state", ""))
                    == "queued_for_merge"
                ):
                    queued_ids.add(result.pr_state.pr_id)
            
            # Reset failed IDs for this pass to allow retries if state changed
            failed_remediation_ids = set()
            
            active_results = [
                r
                for r in results
                if r.pr_state.pr_id not in merged_ids
                and r.pr_state.pr_id not in queued_ids
            ]
            if not active_results:
                print("All PRs processed, merged, or queued.")
                break
            for result in active_results:
                if max_prs > 0 and len(processed_ids) >= max_prs:
                    print(f"Reached max PR limit ({max_prs}); stopping queue drain.")
                    limit_reached = True
                    break
                pr_id = result.pr_state.pr_id
                
                if result.blocked_by_global_fix_pr:
                    print(f"PR #{pr_id}: Blocked pending global fix PR #{result.blocked_by_global_fix_pr}. Skipping remediation.")
                    processed_ids.add(pr_id)
                    continue
                    
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
                        merge_result = pr_merge(
                            argparse.Namespace(
                                **{**vars(args), "id": pr_id, "_queue_lock_held": True}
                            )
                        )
                        if merge_result.lifecycle_state == PRState.MERGED.value or (
                            merge_result.merge_decision
                            and _state_value(merge_result.merge_decision.action)
                            == MergeActionType.AUTO_MERGE_FALLBACK.value
                        ):
                            if merge_result.lifecycle_state == PRState.MERGED.value:
                                merged_ids.add(pr_id)
                            else:
                                queued_ids.add(pr_id)
                    except RuntimeError as e:
                        print(f"Merge error for PR #{pr_id}: {e}")
                        failed_remediation_ids.add(pr_id)
                elif tactic == "APPLY_FIX" and execute:
                    try:
                        apply_result = pr_apply(
                            argparse.Namespace(
                                **{**vars(args), "id": pr_id, "_queue_lock_held": True}
                            )
                        )
                        # Re-derive actions to see if it's merge-ready now
                        if "MERGE" in _derive_allowed_actions(apply_result, policy):
                            merge_result = _merge_prepared_result(
                                args=argparse.Namespace(
                                    **{
                                        **vars(args),
                                        "id": pr_id,
                                        "_queue_lock_held": True,
                                        "execute": True,
                                    }
                                ),
                                client=client,
                                repo_root=repo_root,
                                policy=policy,
                                pr_root=pr_root,
                                active_run_id=active_run_id,
                                prepared_result=apply_result,
                            )
                            if merge_result.lifecycle_state == PRState.MERGED.value or (
                                merge_result.merge_decision
                                and _state_value(merge_result.merge_decision.action)
                                == MergeActionType.AUTO_MERGE_FALLBACK.value
                            ):
                                if merge_result.lifecycle_state == PRState.MERGED.value:
                                    merged_ids.add(pr_id)
                                else:
                                    queued_ids.add(pr_id)
                        
                        # If validation still failed after fix, we don't add to merged_ids, 
                        # so it will be re-scanned in next pass.
                        if not apply_result.validation_report or not apply_result.validation_report.passed:
                            print(f"PR #{pr_id}: Fix attempt completed but validation still failing.")
                            failed_remediation_ids.add(pr_id)

                    except RuntimeError as e:
                        print(f"Apply error for PR #{pr_id}: {e}")
                        failed_remediation_ids.add(pr_id)
                elif tactic == "READY" and execute:
                    try:
                        pr_ready(
                            argparse.Namespace(
                                **{**vars(args), "id": pr_id, "_queue_lock_held": True}
                            )
                        )
                    except RuntimeError as e:
                        print(f"Ready error for PR #{pr_id}: {e}")
                elif tactic == "APPROVE" and execute:
                    try:
                        pr_approve(
                            argparse.Namespace(
                                **{**vars(args), "id": pr_id, "_queue_lock_held": True}
                            )
                        )
                    except RuntimeError as e:
                        print(f"Approval error for PR #{pr_id}: {e}")
            if limit_reached:
                break
        print(f"\nRun ID: {active_run_id}")
        print(f"Processed PRs: {len(processed_ids)}")
        print(f"Merged: {len(merged_ids)}")
        print(f"Queued: {len(queued_ids)}")
        print(f"Artifacts: {run_dir}")
        return 0
    finally:
        if execute:
            release_queue_lock(lock_path)
