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



from .classification import _status_value, _severity_value, _state_value, ensure_transition, classify_pr, risk_score, build_pr_state, lifecycle_for_findings, has_conflicts, CLASS_PRIORITY, VALID_TRANSITIONS
__all__ = ['parse_pr_id_args', 'priority_key', 'build_dependency_edges', 'sort_states', 'apply_priority_preferences', 'snapshot_payload', 'require_clean_worktree', 'acquire_queue_lock', 'release_queue_lock', 'QUEUE_LOCK_PATH']

QUEUE_LOCK_PATH = Path("tmp") / "pr_merge_specialist_queue.lock"

def parse_pr_id_args(values: Sequence[str]) -> List[int]:
    parsed: List[int] = []
    for raw in values:
        for part in raw.split(","):
            token = part.strip()
            if token:
                parsed.append(int(token))
    ordered: List[int] = []
    seen = set()
    for pr_id in parsed:
        if pr_id in seen:
            continue
        seen.add(pr_id)
        ordered.append(pr_id)
    return ordered

def require_clean_worktree(repo_root: Path) -> Tuple[bool, str]:
    result = run_command(["git", "status", "--porcelain"], cwd=repo_root)
    if result.returncode != 0:
        return False, result.stderr.strip() or "Unable to evaluate git status"
    if result.stdout.strip():
        return False, result.stdout.strip()
    return True, ""

def acquire_queue_lock(repo_root: Path, active_run_id: str) -> Tuple[bool, Path, str]:
    lock_path = repo_root / QUEUE_LOCK_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"pid": os.getpid(), "run_id": active_run_id, "started_at": utc_now()}
    if lock_path.exists():
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        existing_pid = int(existing.get("pid", 0) or 0)
        if existing_pid and pid_is_running(existing_pid):
            return (
                False,
                lock_path,
                f"queue-drain lock is already held by pid {existing_pid} (run {existing.get('run_id', 'unknown')})",
            )
        lock_path.unlink()
    fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return True, lock_path, ""

def release_queue_lock(lock_path: Optional[Path]) -> None:
    if lock_path and lock_path.exists():
        lock_path.unlink()

def priority_key(pr: PullRequestState) -> Tuple[int, float, int, str, int]:
    return (
        CLASS_PRIORITY.get(pr.pr_class, 99),
        pr.risk_score,
        pr.diff_size,
        pr.updated_at,
        pr.pr_id,
    )

def build_dependency_edges(states: List[PullRequestState]) -> Dict[int, List[int]]:
    edges: Dict[int, List[int]] = defaultdict(list)
    by_head = {pr.head_ref: pr.pr_id for pr in states if pr.head_ref}
    for pr in states:
        depends_on = by_head.get(pr.base_ref)
        if depends_on and depends_on != pr.pr_id:
            edges[depends_on].append(pr.pr_id)
    return {key: sorted(set(value)) for key, value in edges.items()}

def sort_states(states: List[PullRequestState], strategy: str) -> Tuple[List[PullRequestState], List[QueueOrderingLayer], Dict[int, List[int]], bool]:
    if len(states) <= 3 or strategy == "simple":
        ordered = sorted(states, key=priority_key)
        return ordered, [QueueOrderingLayer(layer=0, pr_ids=[item.pr_id for item in ordered])], {}, False
    edges = build_dependency_edges(states)
    if not edges:
        ordered = sorted(states, key=priority_key)
        return ordered, [QueueOrderingLayer(layer=0, pr_ids=[item.pr_id for item in ordered])], {}, False
    by_id = {item.pr_id: item for item in states}
    indegree: Dict[int, int] = {item.pr_id: 0 for item in states}
    for targets in edges.values():
        for target in targets:
            indegree[target] = indegree.get(target, 0) + 1
    queue: deque[int] = deque(sorted([pid for pid, count in indegree.items() if count == 0], key=lambda pid: priority_key(by_id[pid])))
    ordered_ids: List[int] = []
    layers: List[QueueOrderingLayer] = []
    visited: set[int] = set()
    layer_index = 0
    while queue:
        layer_items = sorted(list(queue), key=lambda pid: priority_key(by_id[pid]))
        queue.clear()
        layers.append(QueueOrderingLayer(layer=layer_index, pr_ids=layer_items))
        layer_index += 1
        for pid in layer_items:
            if pid in visited:
                continue
            visited.add(pid)
            ordered_ids.append(pid)
            for child in edges.get(pid, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
    cycle = len(visited) != len(states)
    if cycle:
        remaining = sorted([item.pr_id for item in states if item.pr_id not in visited], key=lambda pid: priority_key(by_id[pid]))
        layers.append(QueueOrderingLayer(layer=layer_index, pr_ids=remaining))
        ordered_ids.extend(remaining)
    return [by_id[pid] for pid in ordered_ids], layers, edges, cycle

def apply_priority_preferences(states: List[PullRequestState], *, only_ids: Sequence[int], prioritize_ids: Sequence[int]) -> List[PullRequestState]:
    filtered = states
    if only_ids:
        allowed = set(only_ids)
        filtered = [pr for pr in filtered if pr.pr_id in allowed]
    if not prioritize_ids:
        return filtered
    priority_rank = {pr_id: index for index, pr_id in enumerate(prioritize_ids)}
    prioritized = [pr for pr in filtered if pr.pr_id in priority_rank]
    remainder = [pr for pr in filtered if pr.pr_id not in priority_rank]
    prioritized.sort(key=lambda pr: priority_rank[pr.pr_id])
    return prioritized + remainder

def snapshot_payload(states: List[PullRequestState]) -> List[Dict[str, Any]]:
    return [state.to_dict() for state in states]
