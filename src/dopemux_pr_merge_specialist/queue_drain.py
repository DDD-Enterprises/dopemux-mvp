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
from .thread_resolution import latest_comment, contains_marker, has_newer_objection, has_resolution_signal, comment_prefers_conflict_side, is_implementable_comment, decide_thread_disposition, extract_suggestion_block, graphql_escape, graph_reply_to_thread, graph_resolve_thread, _graphql_mutation_ok, _is_rate_limited, _execute_thread_graphql, apply_thread_dispositions
from .conflict import read_file_at_ref, maybe_sync_canonical_file, resolve_conflict_markers, apply_suggestion_to_file, conflict_files, pr_changed_files, scan_files_for_conflict_markers, conflict_excerpt, recent_file_history, build_conflict_analysis, recommend_conflict_strategy
from .merge import checks_green, wait_for_green_checks, checks_blocker_reason, decide_merge_action, run_merge_with_fallback, serialize_check_payload
from .worktree import prepare_worktree, cleanup_worktree, ensure_worktree_matches_pr_head, attempt_rebase
__all__ = ['queue_scan', 'pr_plan', 'pr_apply', 'pr_merge', '_get_ops_engine', '_derive_allowed_actions', 'queue_drain', 'stage_and_push_if_needed', 'update_remaining_pr_bases']

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

def queue_scan(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    manifest = manifest_for_run(active_run_id=active_run_id, mode="queue-scan", repo_root=repo_root, repo_slug=repo_slug, policy=policy)
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
    ordered, layers, edges, cycle = sort_states(apply_priority_preferences(states, only_ids=parse_pr_id_args(getattr(args, "only", []) or []), prioritize_ids=parse_pr_id_args(getattr(args, "prioritize", []) or [])), args.strategy)
    ordered_ids = [state.pr_id for state in ordered]
    write_json(queue_dir / "QUEUE_SNAPSHOT.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "states": snapshot_payload(states), "cache": client.cache_summary()})
    write_json(queue_dir / "ORDERING_PLAN.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "strategy": args.strategy, "cycle_detected": cycle, "layers": [layer.to_dict() for layer in layers], "edges": edges, "ordered_pr_ids": ordered_ids})
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    manifest.completed_phases.append("queue-scan")
    manifest.artifact_pointers.update({"queue_snapshot": str(queue_dir / "QUEUE_SNAPSHOT.json"), "ordering_plan": str(queue_dir / "ORDERING_PLAN.json")})
    write_manifest(run_dir, manifest)
    write_text(run_dir / "RUN_SUMMARY.md", render_operator_summary(results))
    print(f"Open PRs: {len(states)}")
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

def pr_apply(args: argparse.Namespace) -> int:
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
    commands_log = pr_dir / "COMMANDS_RUN.txt"
    write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
    worktree_path: Optional[Path] = None
    branch: Optional[str] = None
    blockers: List[Finding] = []
    thread_dispositions = [decide_thread_disposition(thread, validation_green=pr.ci_status == "SUCCESS", policy=policy) for thread in threads if not thread.is_resolved]
    if args.execute:
        worktree_path, branch, err = prepare_worktree(repo_root, pr.pr_id, active_run_id, commands_log, policy)
        if err or worktree_path is None or branch is None:
            blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="worktree_setup_failed", message=f"worktree setup failed: {err}", source="local_rebase_simulation"))
        else:
            fresh, fresh_reason = ensure_worktree_matches_pr_head(worktree_path=worktree_path, pr_id=pr.pr_id, head_ref=pr.head_ref, client=client, commands_log=commands_log, policy=policy)
            if not fresh:
                blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="stale_worktree_refresh_failed", message=f"worktree freshness check failed: {fresh_reason}", source="local_rebase_simulation"))
            else:
                ok, conflict, message = attempt_rebase(pr_id=pr.pr_id, worktree_path=worktree_path, base_ref=pr.base_ref, head_ref=pr.head_ref, commands_log=commands_log, execute=True, repo=getattr(args, "repo", None), policy=policy)
                if not ok and conflict:
                    write_text(pr_dir / "CONFLICT_ANALYSIS.md", build_conflict_analysis(pr=pr, worktree_path=worktree_path, rebase_error=message, policy=policy))
                    blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type=BlockerType.CONFLICT_DETECTED.value, message="Rebase conflict encountered.", details={"detail": message}, source="local_rebase_simulation"))
                elif not ok:
                    blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="rebase_update_failed", message=f"rebase update failed: {message}", source="local_rebase_simulation"))
                else:
                    applied = apply_thread_dispositions(dispositions=thread_dispositions, threads_by_id={thread.id: thread for thread in threads}, worktree_path=worktree_path, base_ref=pr.base_ref, execute=True, commands_log=commands_log, repo_root=repo_root, policy=policy)
                    thread_dispositions = applied
                    stage_and_push_if_needed(worktree_path=worktree_path, head_ref=pr.head_ref, active_run_id=active_run_id, pr_id=pr.pr_id, execute=True, commands_log=commands_log, policy=policy)
    validation = run_validation(repo_root=repo_root, worktree_path=worktree_path, policy=policy, execute=bool(args.execute), commands_log=commands_log, pr_id=pr.pr_id, head_sha=pr.head_sha, base_sha=pr.base_sha, policy_fingerprint=policy_fingerprint(policy), lifecycle_state="applied" if args.execute else "planned")
    write_text(pr_dir / "VALIDATION.json", json.dumps(validation.to_dict(), indent=2) + "\n")
    write_text(pr_dir / "VALIDATION_REPORT.md", validation_report_md(validation))
    changed_paths: List[str] = []
    if worktree_path and policy.get("conflict_rules", {}).get("scan_changed_files_for_markers", True):
        changed_paths = pr_changed_files(worktree_path, pr.base_ref, commands_log, policy)
    conflict_markers = scan_files_for_conflict_markers(worktree_path, changed_paths) if worktree_path else []
    if conflict_markers:
        blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="conflict_markers_present", message="Conflict markers remain in changed PR files.", details={"paths": conflict_markers}, source="local_rebase_simulation"))
    write_json(pr_dir / "CONFLICT_MARKER_SCAN.json", {"paths": conflict_markers})
    check_payload = client.query_checks(pr.pr_id)
    findings = blockers + findings_from_pr_state(pr, check_payload=check_payload, active_threads=thread_counters(client.fetch_review_threads(pr.pr_id))[1], validation_status=validation.status, local_validation_required=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)))
    result = PRResult(
        run_id=active_run_id,
        pr_state=replace(pr, lifecycle_state=lifecycle_for_findings(findings, validation_status=validation.status)),
        lifecycle_state=lifecycle_for_findings(findings, validation_status=validation.status),
        apply_actions=["prepare worktree", "rebase branch", "apply review thread fixes", "run validation"],
        merge_decision=decide_merge_action(pr=pr, findings=findings, validation_report=validation),
        findings=findings,
        truth_sources=truth_sources_for(check_payload, validation, policy, rebase_status="passed" if not blockers else "failed"),
        precedence_order=TRUTH_PRECEDENCE,
        decision_basis=decision_basis_payload(
            winning_reason="apply_phase_gates",
            winning_sources=["policy", "github_protection", "local_validation", "local_apply_state"],
        ),
        validation_report=validation,
        thread_dispositions=thread_dispositions,
        fingerprint=plan_fingerprint(pr, policy_fp=policy_fingerprint(policy), review_state=serialize_check_payload(check_payload)),
        artifacts={"commands": str(commands_log)},
    )
    write_json(pr_dir / "THREAD_DISPOSITIONS.json", {"applied": [item.to_dict() for item in thread_dispositions]})
    write_json(pr_dir / "APPLY.json", result.to_dict())
    write_pr_state_artifact(pr_dir, result)
    if worktree_path is not None and branch is not None:
        cleanup_worktree(repo_root, worktree_path, branch, commands_log, policy)
    print(f"Apply artifacts: {pr_dir}")
    return 0

def pr_merge(args: argparse.Namespace) -> int:
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
    commands_log = pr_dir / "COMMANDS_RUN.txt"
    apply_result_path = pr_dir / "APPLY.json"
    validation = run_validation(repo_root=repo_root, worktree_path=None, policy=policy, execute=False, commands_log=commands_log, pr_id=pr.pr_id, head_sha=pr.head_sha, base_sha=pr.base_sha, policy_fingerprint=policy_fingerprint(policy), lifecycle_state=PRState.MERGE_READY.value)
    if apply_result_path.exists():
        apply_payload = json.loads(apply_result_path.read_text(encoding="utf-8"))
        validation_payload = apply_payload.get("validation_report")
        if isinstance(validation_payload, dict):
            from .schema import Fingerprint as SchemaFingerprint, ValidationStepResult

            fingerprint_payload_data = validation_payload.get("input_fingerprint")
            validation = ValidationReport(
                status=validation_payload["status"],
                required_for_merge_ready=validation_payload.get("required_for_merge_ready", True),
                steps=[
                    ValidationStepResult(**step)
                    for step in validation_payload.get("steps", [])
                ],
                attempts=validation_payload.get("attempts", 0),
                remediation_applied=validation_payload.get("remediation_applied", False),
                fingerprint=SchemaFingerprint(**fingerprint_payload_data)
                if fingerprint_payload_data
                else None,
            )
    check_green, check_payload, wait_payload = wait_for_green_checks(pr_id=pr.pr_id, client=client, execute=bool(args.execute), policy=policy)
    findings = findings_from_pr_state(pr, check_payload=check_payload, active_threads=active_threads, validation_status=validation.status, local_validation_required=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)))
    if validation.fingerprint is not None and validation.fingerprint.valid_for_sha != pr.head_sha:
        findings.append(
            Finding(
                kind=FindingSeverity.BLOCKER,
                finding_type="stale_validation",
                message="Prior validation artifact is stale for the current PR head SHA.",
                details={
                    "validated_sha": validation.fingerprint.valid_for_sha,
                    "current_sha": pr.head_sha,
                },
                source="local_validation",
            )
        )
    if not check_green:
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="merge_gate", message=checks_blocker_reason(check_payload, wait_payload), source="github_protection_review"))
    decision = decide_merge_action(pr=pr, findings=findings, validation_report=validation)
    merged = run_merge_with_fallback(decision=decision, pr_id=pr.pr_id, execute=bool(args.execute), repo=getattr(args, "repo", None), commands_log=commands_log, repo_root=repo_root, policy=policy, client=client)
    merge_succeeded = _state_value(merged.action) in {MergeActionType.REBASE_MERGE.value, MergeActionType.AUTO_MERGE_FALLBACK.value} and args.execute
    result = PRResult(
        run_id=active_run_id,
        pr_state=replace(pr, lifecycle_state=PRState.MERGED if merge_succeeded else PRState.MERGE_BLOCKED),
        lifecycle_state=PRState.MERGED.value if merge_succeeded else PRState.MERGE_BLOCKED.value,
        apply_actions=[],
        merge_decision=merged,
        findings=findings,
        truth_sources=truth_sources_for(check_payload, validation, policy),
        precedence_order=TRUTH_PRECEDENCE,
        decision_basis=decision_basis_payload(
            winning_reason="remote_merge_gate",
            winning_sources=["policy", "github_protection", "local_validation"],
        ),
        validation_report=validation,
        thread_dispositions=[],
        fingerprint=plan_fingerprint(pr, policy_fp=policy_fingerprint(policy), review_state=serialize_check_payload(check_payload)),
        artifacts={"commands": str(commands_log)},
    )
    write_json(pr_dir / "MERGE.json", {"decision": merged.to_dict(), "checks": serialize_check_payload(check_payload), "check_wait": wait_payload})
    write_json(pr_dir / "RESULT.json", result.to_dict())
    write_pr_state_artifact(pr_dir, result)
    write_json(run_dir / "CHECK_WAIT_REPORT.json", wait_payload)
    print(f"Merge artifacts: {pr_dir}")
    return 0

def _get_ops_engine(args: argparse.Namespace) -> Any:
    from .ops_engine import OperationalizationEngine
    return OperationalizationEngine(Path(args.out_dir) / "ops")


def _derive_allowed_actions(policy: Dict[str, Any], gate: Any) -> List[str]:
    # Placeholder for deriving allowed actions based on policy and current gate state
    return ["MISSION_INTEL", "SEQUENCING", "BLOCKER_SURFACING", "METADATA_PATCHING", "CODE_IMPLEMENTATION", "THREAD_SYNC"]


def queue_drain(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    manifest = manifest_for_run(active_run_id=active_run_id, mode="queue-drain", repo_root=repo_root, repo_slug=repo_slug, policy=policy)
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    lock_path: Optional[Path] = None
    if args.execute:
        if policy.get("gates", {}).get("require_clean_worktree", True) and not getattr(args, "allow_dirty", False):
            clean_ok, clean_detail = require_clean_worktree(repo_root)
            if not clean_ok:
                write_json(run_dir / "PRECHECK.json", {"ok": False, "reason": clean_detail})
                return 2
        acquired, lock_path, reason = acquire_queue_lock(repo_root, active_run_id)
        if not acquired:
            write_json(run_dir / "QUEUE_REPORT.json", {"run_id": active_run_id, "execute": True, "processed": 0, "merged": 0, "blocked": 0, "lock": {"acquired": False, "path": str(lock_path), "reason": reason}})
            print(f"Blocked by active queue worker: {reason}")
            return 2
    results: List[PRResult] = []
    pass_reports: List[Dict[str, Any]] = []
    base_rebase_updates: List[Dict[str, Any]] = []
    merged_ids: List[int] = []
    processed_ids: set[int] = set()
    prioritize_ids = parse_pr_id_args(getattr(args, "prioritize", []) or [])
    only_ids = parse_pr_id_args(getattr(args, "only", []) or [])
    try:
        max_passes = max(int(getattr(args, "max_passes", 1) or 1), 1)
        for pass_index in range(1, max_passes + 1):
            raws = client.fetch_open_prs(int(args.limit))
            states = []
            thread_map: Dict[int, List[ReviewThread]] = {}
            for raw in raws:
                threads = client.fetch_review_threads(int(raw["number"]))
                unresolved_total, active_threads, outdated_threads = thread_counters(threads)
                pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
                states.append(pr)
                thread_map[pr.pr_id] = threads
            states = apply_priority_preferences(states, only_ids=only_ids, prioritize_ids=prioritize_ids)
            ordered, layers, edges, cycle = sort_states(states, args.strategy)
            if args.max_prs and int(args.max_prs) > 0:
                ordered = ordered[: int(args.max_prs)]
            write_json(queue_dir / "QUEUE_SNAPSHOT.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "states": snapshot_payload(states), "cache": client.cache_summary()})
            write_json(queue_dir / "ORDERING_PLAN.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "strategy": args.strategy, "cycle_detected": cycle, "layers": [layer.to_dict() for layer in layers], "edges": edges, "ordered_pr_ids": [pr.pr_id for pr in ordered], "prioritize_ids": prioritize_ids, "only_ids": only_ids})
            if not ordered:
                pass_reports.append({"pass_index": pass_index, "queue_size": 0, "processed": 0, "merged": 0, "healthy_pending_pr_ids": []})
                break
            merged_this_pass = 0
            healthy_pending_ids: List[int] = []
            for index, pr in enumerate(ordered):
                processed_ids.add(pr.pr_id)
                pr_dir = pr_dir_for(pr_root, pr.pr_id)
                write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
                threads = thread_map[pr.pr_id]
                write_json(pr_dir / "REVIEW_THREADS.json", {"threads": [thread.to_dict() for thread in threads]})
                check_payload = client.query_checks(pr.pr_id)
                validation_dry = ValidationReport(
                    status=ValidationStatus.NOT_EXECUTED,
                    required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
                    steps=[],
                    attempts=0,
                    remediation_applied=False,
                )
                plan_result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation_dry, policy=policy, previous_result=results[-1].to_dict() if results else None)
                write_json(pr_dir / "PLAN.json", plan_result.to_dict())
                write_pr_state_artifact(pr_dir, plan_result)
                apply_ns = argparse.Namespace(**{**vars(args), "id": pr.pr_id, "run_id": active_run_id})
                pr_apply(apply_ns)
                client.invalidate(f"pr:{pr.pr_id}")
                client.invalidate(f"threads:{pr.pr_id}")
                merge_ns = argparse.Namespace(**{**vars(args), "id": pr.pr_id, "run_id": active_run_id})
                pr_merge(merge_ns)
                result_path = pr_dir / "RESULT.json"
                if result_path.exists():
                    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
                    merged = result_payload.get("lifecycle_state") == "merged"
                    if merged:
                        merged_ids.append(pr.pr_id)
                        merged_this_pass += 1
                        remaining_ids = [item.pr_id for item in ordered[index + 1 :]]
                        updates = update_remaining_pr_bases(remaining=remaining_ids, execute=bool(args.execute), repo=getattr(args, "repo", None), commands_log=run_dir / "COMMANDS_RUN.txt", repo_root=repo_root, policy=policy)
                        base_rebase_updates.extend([{"trigger_pr": pr.pr_id, "pass_index": pass_index, **item} for item in updates])
                        client.invalidate("open_prs:")
                        break
                    checks = json.loads((pr_dir / "MERGE.json").read_text(encoding="utf-8")) if (pr_dir / "MERGE.json").exists() else {}
                    if checks:
                        pending = int(checks.get("checks", {}).get("required_checks_pending", 0) or 0)
                        failures = int(checks.get("checks", {}).get("required_checks_failed", 0) or 0)
                        if pending > 0 and failures == 0:
                            healthy_pending_ids.append(pr.pr_id)
                if result_path.exists():
                    results.append(PRResult(**_inflate_pr_result(json.loads(result_path.read_text(encoding="utf-8")))))
            pass_reports.append({"pass_index": pass_index, "queue_size": len(ordered), "processed": len(ordered), "merged": merged_this_pass, "healthy_pending_pr_ids": healthy_pending_ids})
            if merged_this_pass == 0 and not healthy_pending_ids:
                break
            client.invalidate("open_prs:")
        manifest.completed_phases.extend(["queue-scan", "pr-plan", "pr-apply", "pr-merge", "queue-drain"])
        manifest.pr_states.update({str(result.pr_state.pr_id): result.lifecycle_state for result in results})
        manifest.artifact_pointers.update({"queue_snapshot": str(queue_dir / "QUEUE_SNAPSHOT.json"), "ordering_plan": str(queue_dir / "ORDERING_PLAN.json"), "base_rebase_updates": str(run_dir / "BASE_REBASE_UPDATES.json")})
        write_manifest(run_dir, manifest)
        write_json(run_dir / "BASE_REBASE_UPDATES.json", base_rebase_updates)
        write_json(
            run_dir / "CHECK_WAIT_REPORT.json",
            {
                "wait_used": any(item.get("healthy_pending_pr_ids") for item in pass_reports),
                "wait_reason": "healthy_required_pending" if any(item.get("healthy_pending_pr_ids") for item in pass_reports) else "no_wait_needed",
                "iterations": len(pass_reports),
                "final_status": "healthy_pending" if any(item.get("healthy_pending_pr_ids") for item in pass_reports) else "stable",
                "passes": pass_reports,
            },
        )
        write_text(run_dir / "RUN_SUMMARY.md", render_operator_summary(results))
        queue_report = {
            "meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(),
            "run_id": active_run_id,
            "execute": bool(args.execute),
            "strategy": args.strategy,
            "prioritize_ids": prioritize_ids,
            "only_ids": only_ids,
            "processed": len(processed_ids),
            "merged": len(merged_ids),
            "blocked": len([result for result in results if result.lifecycle_state != "merged"]),
            "merged_ids": merged_ids,
            "passes": pass_reports,
            "summaries": [result.to_dict() for result in results],
            "cache": client.cache_summary(),
        }
        write_json(run_dir / "QUEUE_REPORT.json", queue_report)
        print(f"Run ID: {active_run_id}")
        print(f"Processed PRs: {len(processed_ids)}")
        print(f"Merged: {len(merged_ids)}")
        print(f"Artifacts: {run_dir}")
        return 0
    finally:
        release_queue_lock(lock_path)
