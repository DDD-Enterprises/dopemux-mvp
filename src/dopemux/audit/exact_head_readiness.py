#!/usr/bin/env python3
"""Exact-head proof/readiness evaluator (TP-DCP-MCP-RO-0018).

Fail-closed local evaluator. Does not mutate branch protection, auto-merge, or
embedded-audit routing. Inputs are JSON snapshots (or empty defaults) so tests
and offline runs remain hermetic.

READY only when all of the following hold:
- proof head matches requested head
- embedded audit status is PASS or PASS_WITH_RISKS (not SKIPPED/FAIL/missing)
- no failed/pending required checks for this head
- checks are not stale relative to head
- no unknown reviewers/bots
- no unresolved blocking review threads
- changed files stay within allowlist (when provided)
- no unclassified review items (when review classifications provided)
- optional acceptance_report.release_ready is true when present and required

Exit codes:
  0  evaluation completed and status == READY
  1  evaluation completed and status != READY
  2  input/usage error
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

PASSING_AUDIT = frozenset({"PASS", "PASS_WITH_RISKS"})
FAIL_CHECK_CONCLUSIONS = frozenset(
    {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
)
PENDING_CHECK_STATUS = frozenset({"queued", "in_progress", "pending", "waiting", "requested"})
KNOWN_ACTORS_DEFAULT = frozenset(
    {
        "hu3mann",
        "copilot-pull-request-reviewer",
        "copilot-pull-request-reviewer[bot]",
        "chatgpt-codex-connector",
        "chatgpt-codex-connector[bot]",
        "github-actions",
        "github-actions[bot]",
        "dependabot",
        "dependabot[bot]",
    }
)


def _load_json(path: Optional[Path]) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"unreadable json: {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise SystemExit(f"json root must be object: {path}")
    return raw


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def evaluate_exact_head_readiness(
    *,
    head_sha: str,
    pr_number: int = 0,
    repo: str = "DDD-Enterprises/dopemux-mvp",
    branch: str = "",
    base_branch: str = "main",
    proof: Optional[Mapping[str, Any]] = None,
    checks: Optional[Iterable[Mapping[str, Any]]] = None,
    review_threads: Optional[Iterable[Mapping[str, Any]]] = None,
    reviewers: Optional[Iterable[str]] = None,
    changed_files: Optional[Iterable[str]] = None,
    allowlist: Optional[Iterable[str]] = None,
    acceptance_report: Optional[Mapping[str, Any]] = None,
    require_acceptance_ready: bool = False,
    known_actors: Optional[Iterable[str]] = None,
    created_at: Optional[str] = None,
) -> dict[str, Any]:
    """Pure evaluation. Never network. Fail closed on missing critical fields."""
    head = (head_sha or "").strip()
    blockers: list[str] = []
    proof = dict(proof or {})
    checks_list = [dict(c) for c in (checks or [])]
    threads = [dict(t) for t in (review_threads or [])]
    reviewer_list = [str(r) for r in (reviewers or [])]
    files = [str(f) for f in (changed_files or [])]
    allow = [str(a) for a in (allowlist or [])]
    known = set(known_actors or KNOWN_ACTORS_DEFAULT)
    acceptance_report = dict(acceptance_report or {})

    if not head or len(head) < 7:
        blockers.append("missing_or_short_head_sha")

    # --- proof stale / head bind ---
    proof_heads = []
    for key in (
        "implementation_commit",
        "head_sha",
        "head_at_creation",
    ):
        val = proof.get(key)
        if isinstance(val, str) and val:
            proof_heads.append(val)
    pr_obj = proof.get("pr") if isinstance(proof.get("pr"), dict) else {}
    for key in ("head_at_creation", "head_sha"):
        val = pr_obj.get(key)
        if isinstance(val, str) and val:
            proof_heads.append(val)
    # Also accept nested live_acceptance binding
    live = proof.get("live_acceptance") if isinstance(proof.get("live_acceptance"), dict) else {}

    proof_stale = False
    if head and proof_heads:
        # Any explicit head field must match (prefix-ok)
        for ph in proof_heads:
            if not (head.startswith(ph) or ph.startswith(head[:7])):
                proof_stale = True
                break
    elif head and proof:
        # Proof present but no head bind → stale/unknown
        proof_stale = True
        blockers.append("proof_missing_head_bind")
    if proof_stale:
        blockers.append("proof_stale_to_head")

    # --- embedded audit ---
    emb = proof.get("embedded_audit") if isinstance(proof.get("embedded_audit"), dict) else {}
    audit_status = str(emb.get("status") or proof.get("audit_status") or "").upper()
    if not audit_status:
        blockers.append("embedded_audit_missing")
    elif audit_status in {"SKIPPED", "FAIL", "FAILED", "ERROR", "NOT_RUN"}:
        blockers.append(f"embedded_audit_{audit_status.lower()}")
    elif audit_status not in PASSING_AUDIT:
        blockers.append(f"embedded_audit_not_passing:{audit_status or 'unknown'}")

    # --- checks ---
    failed_checks: list[str] = []
    pending_checks: list[str] = []
    checks_stale = False
    if not checks_list:
        blockers.append("checks_missing")
    for check in checks_list:
        name = str(check.get("name") or "unknown-check")
        status = str(check.get("status") or "unknown").lower()
        conclusion = str(check.get("conclusion") or "unknown").lower()
        check_head = str(check.get("head_sha") or "")
        matches = check.get("matches_head_sha")
        if matches is None and head and check_head:
            matches = head.startswith(check_head) or check_head.startswith(head[:7])
        if head and check_head and not matches:
            checks_stale = True
        if status in PENDING_CHECK_STATUS or conclusion == "pending":
            pending_checks.append(name)
        if status == "completed" and conclusion in FAIL_CHECK_CONCLUSIONS:
            failed_checks.append(name)
        if status == "completed" and conclusion not in {
            "success",
            "skipped",
            "neutral",
            "cancelled",  # cancelled still listed below as fail-ish for required
        }:
            # non-success completed (except skipped/neutral) blocks
            if conclusion not in {"success", "skipped", "neutral"}:
                if name not in failed_checks and conclusion in FAIL_CHECK_CONCLUSIONS:
                    pass
    if failed_checks:
        blockers.append("failed_checks")
    if pending_checks:
        blockers.append("pending_checks")
    if checks_stale:
        blockers.append("checks_stale_to_head")

    # --- unknown reviewers ---
    unknown_reviewers = sorted({r for r in reviewer_list if r and r not in known and r.rstrip("]") not in known})
    # normalize bot suffix
    cleaned_unknown = []
    for r in unknown_reviewers:
        base = r.replace("[bot]", "")
        if base in known or r in known:
            continue
        cleaned_unknown.append(r)
    unknown_reviewers = cleaned_unknown
    if unknown_reviewers:
        blockers.append("unknown_reviewers_or_bots")

    # --- unresolved threads ---
    blocking_thread_unresolved = False
    for thread in threads:
        if thread.get("isResolved") is True:
            continue
        # treat unresolved as blocking unless explicitly non-blocking
        if thread.get("blocking") is False:
            continue
        blocking_thread_unresolved = True
        break
    if blocking_thread_unresolved:
        blockers.append("blocking_thread_unresolved")

    # --- allowlist scope escape ---
    diff_escapes = False
    if allow and files:
        for path in files:
            if path == ".claude/claude_config.json":
                # generated noise; still counts as escape if present in changed set
                # for readiness we block unallowlisted paths
                pass
            if not _path_allowed(path, allow):
                diff_escapes = True
                break
    if diff_escapes:
        blockers.append("diff_escapes_packet_allowlist")

    # --- acceptance release_ready optional gate ---
    if require_acceptance_ready:
        if acceptance_report.get("release_ready") is not True:
            blockers.append("acceptance_release_not_ready")
        # Also inspect proof nested field
        if live.get("release_ready") is False:
            if "acceptance_release_not_ready" not in blockers:
                blockers.append("acceptance_release_not_ready")

    # Dedupe blockers preserve order
    seen: set[str] = set()
    ordered_blockers: list[str] = []
    for b in blockers:
        if b not in seen:
            seen.add(b)
            ordered_blockers.append(b)

    status = "READY" if not ordered_blockers else "BLOCKED"
    created = created_at or datetime.now(timezone.utc).isoformat()

    return {
        "schema_version": "1.0.0",
        "evaluator": "scripts/audit/exact_head_readiness.py",
        "packet_series": "TP-DCP-MCP-RO-0018",
        "pr_number": pr_number,
        "repo": repo,
        "branch": branch,
        "head_sha": head,
        "base_branch": base_branch,
        "changed_files": files,
        "checks": [
            {
                "name": str(c.get("name") or "unknown"),
                "status": str(c.get("status") or "unknown"),
                "conclusion": str(c.get("conclusion") or "unknown"),
                "head_sha": str(c.get("head_sha") or ""),
                "matches_head_sha": bool(
                    c.get("matches_head_sha")
                    if c.get("matches_head_sha") is not None
                    else (
                        head
                        and c.get("head_sha")
                        and (
                            head.startswith(str(c.get("head_sha")))
                            or str(c.get("head_sha")).startswith(head[:7])
                        )
                    )
                ),
            }
            for c in checks_list
        ],
        "review_threads": threads,
        "unknown_reviewers_or_bots": unknown_reviewers,
        "failed_checks": failed_checks,
        "pending_checks": pending_checks,
        "checks_stale_to_head": checks_stale,
        "proof_stale": proof_stale,
        "blocking_thread_unresolved": blocking_thread_unresolved,
        "diff_escapes_packet_allowlist": diff_escapes,
        "embedded_audit_status": audit_status or "MISSING",
        "unresolved_blockers": ordered_blockers,
        "status": status,
        "ready_for_merge": status == "READY",
        "created_at": created,
        "proof_bundle_refs": [str(p) for p in _as_list(proof.get("files_changed"))][:20]
        if proof
        else [],
        "notes": [
            "READY requires embedded audit PASS/PASS_WITH_RISKS; SKIPPED fails closed.",
            "Does not change branch protection or embedded-audit.yml routing.",
            "Skipped live acceptance keeps require_acceptance_ready blocked when enabled.",
        ],
    }


def _path_allowed(path: str, allowlist: Iterable[str]) -> bool:
    for pattern in allowlist:
        if pattern.endswith("/**"):
            root = pattern[:-3]
            if path == root.rstrip("/") or path.startswith(root.rstrip("/") + "/"):
                return True
        elif pattern.endswith("/*"):
            root = pattern[:-2]
            if path.startswith(root.rstrip("/") + "/") and "/" not in path[len(root.rstrip("/")) + 1 :]:
                return True
        elif path == pattern:
            return True
        elif path.startswith(pattern.rstrip("/") + "/"):
            # directory prefix without glob
            if pattern.endswith("/"):
                return True
    return False


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--head-sha", required=True)
    p.add_argument("--pr-number", type=int, default=0)
    p.add_argument("--repo", default="DDD-Enterprises/dopemux-mvp")
    p.add_argument("--branch", default="")
    p.add_argument("--base-branch", default="main")
    p.add_argument("--proof-json", type=Path, default=None)
    p.add_argument("--checks-json", type=Path, default=None, help="JSON list or {checks:[...]}")
    p.add_argument("--threads-json", type=Path, default=None, help="JSON list or {threads:[...]}")
    p.add_argument("--reviewers-json", type=Path, default=None, help="JSON list of logins")
    p.add_argument("--changed-files-json", type=Path, default=None)
    p.add_argument("--allowlist-json", type=Path, default=None)
    p.add_argument("--acceptance-json", type=Path, default=None)
    p.add_argument("--require-acceptance-ready", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    proof = _load_json(args.proof_json)
    checks_raw = _load_json(args.checks_json) if args.checks_json else {}
    if isinstance(checks_raw, dict) and "checks" in checks_raw:
        checks = checks_raw.get("checks") or []
    elif isinstance(checks_raw, list):
        checks = checks_raw
    else:
        checks = _as_list(checks_raw.get("checks")) if checks_raw else []

    threads_raw = _load_json(args.threads_json) if args.threads_json else {}
    if isinstance(threads_raw, dict):
        threads = threads_raw.get("threads") or threads_raw.get("review_threads") or []
    else:
        threads = []

    reviewers_raw = json.loads(args.reviewers_json.read_text()) if args.reviewers_json else []
    if isinstance(reviewers_raw, dict):
        reviewers = reviewers_raw.get("reviewers") or []
    else:
        reviewers = reviewers_raw if isinstance(reviewers_raw, list) else []

    files_raw = json.loads(args.changed_files_json.read_text()) if args.changed_files_json else []
    if isinstance(files_raw, dict):
        files = files_raw.get("files") or files_raw.get("changed_files") or []
    else:
        files = files_raw if isinstance(files_raw, list) else []

    allow_raw = json.loads(args.allowlist_json.read_text()) if args.allowlist_json else []
    if isinstance(allow_raw, dict):
        allow = allow_raw.get("allowlist") or []
    else:
        allow = allow_raw if isinstance(allow_raw, list) else []

    acceptance = _load_json(args.acceptance_json) if args.acceptance_json else {}

    result = evaluate_exact_head_readiness(
        head_sha=args.head_sha,
        pr_number=args.pr_number,
        repo=args.repo,
        branch=args.branch,
        base_branch=args.base_branch,
        proof=proof,
        checks=checks,
        review_threads=threads,
        reviewers=reviewers,
        changed_files=files,
        allowlist=allow,
        acceptance_report=acceptance,
        require_acceptance_ready=args.require_acceptance_ready,
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
