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
    "read_file_at_ref",
    "maybe_sync_canonical_file",
    "resolve_conflict_markers",
    "apply_suggestion_to_file",
    "comment_prefers_conflict_side",
    "extract_suggestion_block",
    "conflict_files",
    "pr_changed_files",
    "scan_files_for_conflict_markers",
    "conflict_excerpt",
    "recent_file_history",
    "build_conflict_analysis",
    "recommend_conflict_strategy",
    "conflict_recovery_policy",
    "conflict_recovery_state",
    "safe_conflict_surface",
]


DEFAULT_CONFLICT_RECOVERY_POLICY = {
    "require_opt_in_label": True,
    "opt_in_labels": ["conflict:mechanical"],
    "blocked_labels": ["conflict:semantic"],
    "max_conflict_files": 5,
    "prefer_side": "theirs",
    "safe_path_prefixes": ["docs/", "tests/"],
    "safe_filenames": [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "uv.lock",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
    ],
}


def conflict_recovery_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    configured = (
        policy.get("conflict_rules", {}).get("auto_recovery", {}) or {}
    )
    merged = dict(DEFAULT_CONFLICT_RECOVERY_POLICY)
    for key, value in configured.items():
        merged[key] = value
    merged["opt_in_labels"] = [str(item) for item in merged.get("opt_in_labels", [])]
    merged["blocked_labels"] = [
        str(item) for item in merged.get("blocked_labels", [])
    ]
    merged["safe_path_prefixes"] = [
        str(item) for item in merged.get("safe_path_prefixes", [])
    ]
    merged["safe_filenames"] = [
        str(item) for item in merged.get("safe_filenames", [])
    ]
    merged["max_conflict_files"] = int(merged.get("max_conflict_files", 5) or 5)
    merged["require_opt_in_label"] = bool(
        merged.get("require_opt_in_label", True)
    )
    merged["prefer_side"] = str(merged.get("prefer_side", "theirs") or "theirs")
    return merged


def conflict_recovery_state(pr: PullRequestState, policy: Dict[str, Any]) -> str:
    labels = {label.strip() for label in pr.labels if label}
    config = conflict_recovery_policy(policy)
    if labels & set(config["blocked_labels"]):
        return "semantic_conflict_blocked"
    if labels & set(config["opt_in_labels"]):
        return "eligible"
    if config["require_opt_in_label"]:
        return "manual_conflict_required"
    return "eligible"


def safe_conflict_surface(
    rel_paths: Sequence[str], policy: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    config = conflict_recovery_policy(policy)
    safe_prefixes = tuple(config["safe_path_prefixes"])
    safe_filenames = set(config["safe_filenames"])
    unsafe = [
        rel_path
        for rel_path in rel_paths
        if Path(rel_path).name not in safe_filenames
        and not any(rel_path.startswith(prefix) for prefix in safe_prefixes)
    ]
    return not unsafe, unsafe


def comment_prefers_conflict_side(body: str) -> Optional[str]:
    lowered = html.unescape(body).lower()
    if "<<<<<<< head" not in lowered and "conflict marker" not in lowered:
        return None
    head_markers = [
        "keep the head side",
        "from the <code>head</code> side",
        "keep the current main version",
        "keep the current version",
        "keep the wrapper implementation already in head",
        "between <code><<<<<<< head</code> and <code>=======</code>",
        "under <code><<<<<<< head</code>",
    ]
    if any(marker in lowered for marker in head_markers):
        return "head"
    if "after <code>=======</code>" in lowered or "keep the other side" in lowered:
        return "theirs"
    return None

def extract_suggestion_block(body: str) -> Optional[str]:
    match = re.search(r"```suggestion\s*(.*?)```", body, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip("\n")


def read_file_at_ref(worktree_path: Path, ref: str, rel_path: str) -> Optional[str]:
    result = run_command(["git", "show", f"{ref}:{rel_path}"], cwd=worktree_path)
    if result.returncode != 0:
        return None
    return result.stdout


def maybe_sync_canonical_file(
    *,
    worktree_path: Path,
    base_ref: str,
    rel_path: str,
    original: str,
    resolved: str,
    prefer: str,
    comment_body: str,
    policy: Dict[str, Any],
) -> Tuple[str, str]:
    if prefer != "head":
        return resolved, ""
    canonical_markers = policy.get("conflict_rules", {}).get(
        "canonical_head_markers", []
    )
    if not contains_marker(comment_body, canonical_markers):
        return resolved, ""
    canonical = read_file_at_ref(worktree_path, f"origin/{base_ref}", rel_path)
    if canonical is None:
        return resolved, ""
    if any(marker in canonical for marker in ("<<<<<<<", "=======", ">>>>>>>")):
        return resolved, ""
    if canonical.rstrip("\n") == resolved.rstrip("\n") or canonical.rstrip(
        "\n"
    ) in original.rstrip("\n"):
        return canonical, " using canonical base file content"
    return resolved, ""


def resolve_conflict_markers(text: str, *, prefer: str) -> Tuple[bool, str]:
    if "<<<<<<<" not in text:
        return False, "File does not contain Git conflict markers."
    lines = text.splitlines()
    output: List[str] = []
    index = 0
    changed = False
    while index < len(lines):
        line = lines[index]
        if not line.startswith("<<<<<<<"):
            output.append(line)
            index += 1
            continue
        changed = True
        index += 1
        head_lines: List[str] = []
        while index < len(lines) and not lines[index].startswith("======="):
            head_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            return False, "Malformed conflict block: missing ======= marker."
        index += 1
        other_lines: List[str] = []
        while index < len(lines) and not lines[index].startswith(">>>>>>>"):
            other_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            return False, "Malformed conflict block: missing >>>>>>> marker."
        output.extend(head_lines if prefer == "head" else other_lines)
        index += 1
    resolved = "\n".join(output)
    if text.endswith("\n"):
        resolved += "\n"
    return changed, resolved


def apply_suggestion_to_file(
    *,
    worktree_path: Path,
    thread: ReviewThread,
    comment: ThreadComment,
    base_ref: str,
    policy: Dict[str, Any],
) -> Tuple[bool, str]:
    target = comment.path or thread.path
    if not target:
        return False, "No path on thread/comment."
    file_path = worktree_path / target
    if not file_path.exists() or not file_path.is_file():
        return False, f"Target file missing: {target}"
    original = file_path.read_text(encoding="utf-8")
    text = original
    preferred_conflict_side = comment_prefers_conflict_side(comment.body)
    if preferred_conflict_side is not None:
        changed, resolved = resolve_conflict_markers(
            text, prefer=preferred_conflict_side
        )
        if not changed:
            return False, resolved
        resolved, canonical_note = maybe_sync_canonical_file(
            worktree_path=worktree_path,
            base_ref=base_ref,
            rel_path=target,
            original=original,
            resolved=resolved,
            prefer=preferred_conflict_side,
            comment_body=comment.body,
            policy=policy,
        )
        if resolved == original:
            return False, "Conflict-marker resolution produced no file changes."
        file_path.write_text(resolved, encoding="utf-8")
        return (
            True,
            f"Resolved conflict markers in {target} using {preferred_conflict_side} side{canonical_note}.",
        )
    suggestion = extract_suggestion_block(comment.body)
    if suggestion is not None:
        start = thread.original_start_line or thread.original_line or thread.line
        end = thread.original_line or thread.line or start
        if start is None or end is None:
            return False, "Suggestion block missing line anchors."
        lines = text.splitlines()
        start_idx = max(start - 1, 0)
        end_idx = max(end, start_idx + 1)
        replacement = suggestion.splitlines()
        text = "\n".join(lines[:start_idx] + replacement + lines[end_idx:]) + (
            "\n" if original.endswith("\n") else ""
        )
    else:
        replace_match = re.search(
            r"change\s+<code>(.*?)</code>\s+to\s+<code>(.*?)</code>",
            comment.body,
            re.IGNORECASE | re.DOTALL,
        )
        if replace_match:
            old = html.unescape(replace_match.group(1)).strip()
            new = html.unescape(replace_match.group(2)).strip()
            if old not in text:
                return False, "Could not locate replacement source fragment in file."
            text = text.replace(old, new, 1)
        else:
            delete_match = re.search(
                r"(?:delete|remove)\s+(?:the\s+)?(?:line\s+)?<code>(.*?)</code>",
                comment.body,
                re.IGNORECASE | re.DOTALL,
            )
            if not delete_match:
                return False, "No known machine-applicable suggestion pattern."
            snippet = html.unescape(delete_match.group(1)).strip()
            removed = False
            new_lines: List[str] = []
            for line in text.splitlines():
                if not removed and line.strip() == snippet:
                    removed = True
                    continue
                new_lines.append(line)
            if not removed:
                return False, "Could not find deletion snippet in file."
            text = "\n".join(new_lines) + ("\n" if original.endswith("\n") else "")
    if text == original:
        return False, "No file changes produced."
    file_path.write_text(text, encoding="utf-8")
    return True, f"Applied suggestion to {target}."


def conflict_files(worktree_path: Path, policy: Dict[str, Any]) -> List[str]:
    status = run_command(
        ["git", "status", "--porcelain"],
        cwd=worktree_path,
        timeout_seconds=int(
            policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
        ),
    )
    if status.returncode != 0:
        return []
    return [
        line[3:].strip()
        for line in status.stdout.splitlines()
        if line.startswith(("UU ", "AA ", "DD "))
    ]


def pr_changed_files(
    worktree_path: Path,
    base_ref: str,
    commands_log: Optional[Path],
    policy: Dict[str, Any],
) -> List[str]:
    fetch = run_command(
        ["git", "fetch", "origin", base_ref],
        cwd=worktree_path,
        timeout_seconds=int(
            policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
        ),
    )
    if commands_log:
        append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return []
    diff = run_command(
        ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
        cwd=worktree_path,
        timeout_seconds=int(
            policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
        ),
    )
    if commands_log:
        append_command_log(commands_log, diff)
    if diff.returncode != 0:
        return []
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def scan_files_for_conflict_markers(
    worktree_path: Path, rel_paths: Sequence[str]
) -> List[str]:
    hits: List[str] = []
    conflict_pattern = re.compile(
        r"^<<<<<<< .*\n(?:.*\n)*?^=======\n(?:.*\n)*?^>>>>>>> .*$", re.MULTILINE
    )
    for rel_path in rel_paths:
        file_path = worktree_path / rel_path
        if not file_path.exists() or not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if conflict_pattern.search(text):
            hits.append(rel_path)
    return sorted(set(hits))


def conflict_excerpt(
    worktree_path: Path, rel_path: str, *, context_lines: int = 3
) -> str:
    file_path = worktree_path / rel_path
    if not file_path.exists() or not file_path.is_file():
        return "File unavailable for conflict excerpt."
    lines = file_path.read_text(encoding="utf-8").splitlines()
    excerpts: List[str] = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith("<<<<<<<"):
            index += 1
            continue
        start = max(index - context_lines, 0)
        end = min(index + 1, len(lines))
        while end < len(lines) and not lines[end].startswith(">>>>>>>"):
            end += 1
        if end < len(lines):
            end += 1
        end = min(end + context_lines, len(lines))
        excerpts.append(
            "\n".join(
                f"{line_no + 1:>4}: {content}"
                for line_no, content in enumerate(lines[start:end], start=start)
            )
        )
        index = end
        if len(excerpts) >= 2:
            break
    return (
        "\n\n".join(excerpts)
        if excerpts
        else "No conflict markers found in working tree file."
    )


def recent_file_history(
    worktree_path: Path, rel_path: str, *, limit: int, policy: Dict[str, Any]
) -> List[str]:
    result = run_command(
        ["git", "log", "--oneline", f"-n{limit}", "--", rel_path],
        cwd=worktree_path,
        timeout_seconds=int(
            policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
        ),
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def recommend_conflict_strategy(
    *,
    conflict_file_paths: List[str],
    rebase_error: str,
    pr: PullRequestState,
) -> Tuple[str, str]:
    """Return (strategy_id, rationale) based on conflict characteristics."""

    # Heuristic: migration files present -> MIGRATION_FIRST_THEN_FEATURE_REPLAY
    migration_patterns = ("migration", "alembic", "migrate", "schema")
    if any(
        p
        for p in conflict_file_paths
        if any(m in p.lower() for m in migration_patterns)
    ):
        return (
            "MIGRATION_FIRST_THEN_FEATURE_REPLAY",
            "Conflict involves migration files",
        )

    # Heuristic: interface/API files -> INTERFACE_FIRST_RECONCILIATION
    interface_patterns = (
        "__init__.py",
        "types.ts",
        "types.py",
        "schema",
        "api",
        "interface",
        ".d.ts",
    )
    if any(
        p
        for p in conflict_file_paths
        if any(m in p.lower() for m in interface_patterns)
    ):
        return (
            "INTERFACE_FIRST_RECONCILIATION",
            "Conflict involves interface/API surface files",
        )

    # Heuristic: high file count -> STAGED_SEQUENCE_MERGE
    if len(conflict_file_paths) > 5:
        return (
            "STAGED_SEQUENCE_MERGE",
            f"Large conflict surface ({len(conflict_file_paths)} files)",
        )

    # Heuristic: test files only -> PATCH_ISOLATION_PLAN
    if conflict_file_paths and all("test" in p.lower() for p in conflict_file_paths):
        return "PATCH_ISOLATION_PLAN", "Conflicts isolated to test files"

    # Heuristic: if rebase error suggests complex history -> REVERT_AND_REINTEGRATE
    if (
        "could not apply" in rebase_error.lower()
        or "multiple conflicts" in rebase_error.lower()
    ):
        return (
            "REVERT_AND_REINTEGRATE",
            "Complex rebase failure suggests history rewrite needed",
        )

    # Heuristic: Semantic Risk / High-Risk Path Divergence
    # Escalation path for sensitive files
    unsafe_patterns = ("auth/", "secrets/", "security/", "middleware/", "permission", "encryption", "legal/")
    if any(
        p
        for p in conflict_file_paths
        if any(u in p.lower() for u in unsafe_patterns)
    ):
        return (
            "ESCALATE_FOR_HUMAN_REVIEW",
            "Conflict touches security-sensitive or core architectural middleware",
        )

    # Default: simplest strategy
    return "OURS_THEN_PORT_SELECTIVE", "Standard conflict resolution (default)"


def build_conflict_analysis(
    *,
    pr: PullRequestState,
    worktree_path: Optional[Path],
    rebase_error: str,
    policy: Dict[str, Any],
) -> str:
    strict = bool(policy.get("conflict_rules", {}).get("strict", True))
    lines = [
        f"# Conflict Analysis for PR #{pr.pr_id}",
        "",
        "## Classification",
        "- conflict_type: semantic_or_unknown",
        f"- strict_conflicts: {strict}",
        "",
        "## PR Context",
        f"- title: {pr.title}",
        f"- base_ref: {pr.base_ref}",
        f"- head_ref: {pr.head_ref}",
        f"- merge_state_status: {pr.merge_state_status}",
        f"- ci_status: {pr.ci_status}",
        "",
        "## Rebase Failure Signal",
        "```text",
        rebase_error or "no error text available",
        "```",
        "",
        "## Deep Inspection Protocol",
        "1. Inspect conflict hunks (base/ours/theirs) and surrounding commit intent.",
        "2. Compare behavior impact, not text-only resolution convenience.",
        "3. Reject blanket `-X ours/-X theirs` strategies.",
        "4. Require scoped tests plus full validation when conflict touches shared primitives.",
        "5. Escalate if confidence is below release safety threshold.",
        "",
    ]
    file_paths = []
    if worktree_path:
        files = conflict_files(worktree_path, policy)
        file_paths = files
        lines.extend(
            [
                "## Conflicting Files",
                *([f"- {item}" for item in files] if files else ["- none detected"]),
                "",
            ]
        )
        if files:
            lines.append("## Conflict Hunks")
            for rel_path in files:
                lines.extend(
                    [
                        f"### {rel_path}",
                        "```text",
                        conflict_excerpt(worktree_path, rel_path),
                        "```",
                        "",
                    ]
                )
            lines.append("## Recent File History")
            for rel_path in files:
                history = recent_file_history(
                    worktree_path, rel_path, limit=5, policy=policy
                )
                lines.append(f"### {rel_path}")
                lines.extend(
                    [f"- {entry}" for entry in history]
                    if history
                    else ["- no recent history available"]
                )
                lines.append("")

    # Add strategy recommendation
    strategy_id, rationale = recommend_conflict_strategy(
        conflict_file_paths=file_paths,
        rebase_error=rebase_error,
        pr=pr,
    )
    strategy = STRATEGY_LIBRARY.get(strategy_id)
    if strategy:
        lines.append("")
        lines.append("## Recommended Strategy")
        lines.append(f"**{strategy.name}** (`{strategy_id}`)")
        lines.append(f"- Rationale: {rationale}")
        lines.append(f"- Risk: {strategy.risk_profile}")
        lines.append(f"- Verification: {strategy.verification_burden}")
        lines.append(f"- When to use: {strategy.use_case}")
        lines.append("")

    lines.extend(
        [
            "## Resolution Decision",
            "- status: escalated",
            "- reason: strict conflict mode requires explicit semantic resolution evidence.",
        ]
    )
    return "\n".join(lines) + "\n"
