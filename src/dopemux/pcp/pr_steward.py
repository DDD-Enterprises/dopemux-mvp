"""
Generic PCP-Core PR Steward proof-readiness intake.

Harvests PR state (read-only) and emits a MERGE_READINESS signal with explicit
BLOCKED reasons.  This module is ADVISORY — it NEVER mutates any resource, sets PR state,
or triggers a merge.  READY is fail-closed: withheld on ANY blocking condition.

Green CI is NOT semantic proof (see AIR Red Lines #7/#8).

This is the generic, project-agnostic PCP Core.  The Dopemux-specific
pr-merge-specialist skill (tools/pr_steward/, .claude/skills/) and the OpenClaw
DCP routing contracts (contracts/openclaw-dcp-routing/pr_steward_merge_readiness.
schema.json) *specialise* this core — they co-exist with it rather than replacing
it.

Usage::

    from dopemux.pcp.pr_steward import assess_merge_readiness, harvest_pr_intake

    intake_result = harvest_pr_intake(123, repo="owner/repo")
    signal = assess_merge_readiness(
        intake_result["intake"],
        pr_ref=intake_result["pr_ref"],
        head_sha=intake_result["head_sha"],
        created_at="2026-06-22T00:00:00Z",
    )
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Callable

from jsonschema import Draft202012Validator

from ._schemas import load_schema

# ---------------------------------------------------------------------------
# Schema — loaded from bundled package data (dopemux.pcp._schemas) so the
# validator is available both from the source tree and from an installed wheel.
# No repo-root-relative path is assumed.
# ---------------------------------------------------------------------------
_SCHEMA: dict = load_schema("merge_readiness.schema.json")

_VALIDATOR = Draft202012Validator(_SCHEMA)

_INTAKE_COMPLETENESS_CATEGORIES = (
    "pr_metadata",
    "head_sha",
    "changed_files",
    "commits",
    "reviews",
    "review_comments",
    "review_threads",
    "issue_comments",
    "checks",
    "proof_refs",
    "proof_freshness",
    "reviewer_classifications",
    "allowlist",
    "security_release_approval",
)

# ---------------------------------------------------------------------------
# Write-operation prohibition — this module is READ-ONLY.
# No merge, push, commit, or PR-state-mutation commands are issued here.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Internal helper — injectable subprocess runner for gh CLI calls
# ---------------------------------------------------------------------------

def _default_runner(args: list[str]) -> str:
    """Invoke ``gh`` read-only and return stripped stdout.

    Hardened against path injection: no shell, explicit executable list.
    Only ``gh pr view`` calls (read-only) are issued.

    Raises
    ------
    ValueError
        If ``gh`` returns a non-zero exit code or is unavailable.
    """
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError(
            f"gh CLI not found; cannot harvest PR intake: {exc}"
        ) from exc

    if result.returncode != 0:
        raise ValueError(
            f"gh command failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _derive_intake_completeness(intake: dict) -> dict[str, str]:
    explicit = intake.get("intake_completeness")
    if not isinstance(explicit, dict):
        explicit = {}

    completeness: dict[str, str] = {}
    for category in _INTAKE_COMPLETENESS_CATEGORIES:
        value = explicit.get(category, "MISSING")
        if value not in {"COMPLETE", "MISSING", "UNKNOWN", "NOT_REQUIRED"}:
            value = "UNKNOWN"
        completeness[category] = value
    return completeness


# ---------------------------------------------------------------------------
# Public API: assess_merge_readiness
# ---------------------------------------------------------------------------

def assess_merge_readiness(
    intake: dict | None,
    *,
    pr_ref: dict,
    head_sha: str,
    created_at: str,
) -> dict:
    """Compute the MERGE_READINESS signal from harvested *intake*.

    This is a **pure**, **fail-closed** function.  All inputs are inspected;
    ``blocked_reasons`` is accumulated; ``status`` is derived from that list.
    Nothing is written, merged, or mutated.

    Parameters
    ----------
    intake:
        Harvested evidence dict (matches the ``intake`` sub-object of
        ``merge_readiness.schema.json``).  If ``None`` or missing required
        fields, ``MISSING_REQUIRED_INTAKE`` is added.
    pr_ref:
        PR identity: ``{repo, number, head_ref, base_ref}``.
    head_sha:
        The PR head commit SHA (40 or 64 hex chars).
    created_at:
        ISO 8601 datetime string for when the signal was assembled.

    Returns
    -------
    dict
        A dict satisfying ``schemas/project_control_plane/merge_readiness.schema.json``.

    Raises
    ------
    jsonschema.ValidationError
        If the assembled signal does not satisfy the schema (defensive; should
        not occur in normal operation when inputs are well-formed).
    """
    blocked: list[str] = []

    # ------------------------------------------------------------------
    # Guard: missing/invalid intake OR empty head_sha → MISSING_REQUIRED_INTAKE
    # Appended AT MOST once even when both conditions hold.
    # ------------------------------------------------------------------
    _intake_missing = not isinstance(intake, dict) or not intake
    if _intake_missing or not head_sha:
        blocked.append("MISSING_REQUIRED_INTAKE")
    if not isinstance(intake, dict):
        intake = {}

    intake_completeness = _derive_intake_completeness(intake)
    if any(state != "COMPLETE" for state in intake_completeness.values()):
        blocked.append("INCOMPLETE_INTAKE")

    # ------------------------------------------------------------------
    # Rule 1: proof_freshness != FRESH → STALE_PROOF
    # ------------------------------------------------------------------
    proof_freshness = intake.get("proof_freshness", "UNKNOWN")
    if proof_freshness != "FRESH":
        if "STALE_PROOF" not in blocked:
            blocked.append("STALE_PROOF")

    # ------------------------------------------------------------------
    # Rule 2: any check conclusion == FAILURE → FAILED_CHECK
    # ------------------------------------------------------------------
    checks: list[dict] = intake.get("checks", [])
    if any(c.get("conclusion") == "FAILURE" for c in checks):
        blocked.append("FAILED_CHECK")

    # ------------------------------------------------------------------
    # Rule 3: any check stale_to_head truthy or conclusion in
    #         {STALE, PENDING, UNKNOWN} → STALE_CHECK
    # ------------------------------------------------------------------
    stale_conclusions = {"STALE", "PENDING", "UNKNOWN"}
    if any(
        bool(c.get("stale_to_head")) or c.get("conclusion") in stale_conclusions
        for c in checks
    ):
        blocked.append("STALE_CHECK")

    # ------------------------------------------------------------------
    # Rule 4: any reviewer_classification kind == UNKNOWN →
    #         UNKNOWN_REVIEWER_OR_BOT
    # ------------------------------------------------------------------
    reviewer_classifications: list[dict] = intake.get("reviewer_classifications", [])
    if any(rc.get("kind") == "UNKNOWN" for rc in reviewer_classifications):
        blocked.append("UNKNOWN_REVIEWER_OR_BOT")

    # ------------------------------------------------------------------
    # Rule 5: non-empty unclassified_review_items →
    #         UNCLASSIFIED_REVIEW_ITEM
    # ------------------------------------------------------------------
    unclassified: list[str] = intake.get("unclassified_review_items", [])
    if unclassified:
        blocked.append("UNCLASSIFIED_REVIEW_ITEM")

    # ------------------------------------------------------------------
    # Rule 6: any review_thread with blocking truthy and resolved falsy →
    #         UNRESOLVED_BLOCKING_THREAD
    # ------------------------------------------------------------------
    review_threads: list[dict] = intake.get("review_threads", [])
    if any(
        bool(t.get("blocking")) and not bool(t.get("resolved"))
        for t in review_threads
    ):
        blocked.append("UNRESOLVED_BLOCKING_THREAD")

    # ------------------------------------------------------------------
    # Rule 7: diff_escapes_allowlist truthy → DIFF_OUTSIDE_ALLOWLIST
    # ------------------------------------------------------------------
    if bool(intake.get("diff_escapes_allowlist")):
        blocked.append("DIFF_OUTSIDE_ALLOWLIST")

    # ------------------------------------------------------------------
    # Rule 8: security_release_required truthy and
    #         security_release_approved falsy →
    #         MISSING_SECURITY_RELEASE_APPROVAL
    # (bool() coercion prevents is-True identity bypass, e.g. integer 1)
    # ------------------------------------------------------------------
    if bool(intake.get("security_release_required")) and not bool(
        intake.get("security_release_approved")
    ):
        blocked.append("MISSING_SECURITY_RELEASE_APPROVAL")

    # ------------------------------------------------------------------
    # Derive status
    # ------------------------------------------------------------------
    if not blocked:
        status = "READY"
    elif blocked == ["MISSING_SECURITY_RELEASE_APPROVAL"]:
        # Ambiguous authority requirement → escalate to supervisor
        status = "NEEDS_SUPERVISOR"
    else:
        status = "BLOCKED"

    # ------------------------------------------------------------------
    # Ensure intake has all required fields for schema compliance
    # ------------------------------------------------------------------
    canonical_intake: dict[str, Any] = {
        "changed_files": intake.get("changed_files", []),
        "intake_completeness": intake_completeness,
        "commits": intake.get("commits", []),
        "checks": checks,
        "reviews": intake.get("reviews", []),
        "review_threads": review_threads,
        "reviewer_classifications": reviewer_classifications,
        "unclassified_review_items": unclassified,
        "proof_refs": intake.get("proof_refs", []),
        "proof_freshness": proof_freshness,
        "diff_escapes_allowlist": bool(intake.get("diff_escapes_allowlist", False)),
        "security_release_required": bool(
            intake.get("security_release_required", False)
        ),
        "security_release_approved": bool(
            intake.get("security_release_approved", False)
        ),
    }

    signal: dict[str, Any] = {
        "schema_version": "pcp.merge_readiness.v0",
        "pr_ref": pr_ref,
        "head_sha": head_sha if head_sha else "0" * 40,
        "status": status,
        "blocked_reasons": blocked,
        "intake": canonical_intake,
        "advisory": True,
        "created_at": created_at,
    }

    # ------------------------------------------------------------------
    # Defensive schema validation before returning
    # ------------------------------------------------------------------
    _VALIDATOR.validate(signal)

    return signal


# ---------------------------------------------------------------------------
# Public API: harvest_pr_intake
# ---------------------------------------------------------------------------

def harvest_pr_intake(
    pr_number: int,
    *,
    repo: str,
    runner: Callable[[list[str]], str] | None = None,
) -> dict:
    """Harvest PR intake from GitHub (read-only) using the ``gh`` CLI.

    The *runner* parameter is injectable for testing — pass a callable that
    accepts a ``list[str]`` of args and returns stdout as a string.  In
    production the default subprocess wrapper is used; no live ``gh`` calls
    are made in tests when a fake runner is supplied.

    Only read-only ``gh pr view`` commands are issued.  No write commands
    are ever called — this function is strictly read-only.

    Parameters
    ----------
    pr_number:
        Pull request number to harvest.
    repo:
        Repository in ``owner/repo`` form (required by ``gh``).
    runner:
        Callable that takes ``list[str]`` (the full command including ``gh``)
        and returns stdout.  Defaults to a subprocess wrapper.

    Returns
    -------
    dict
        A dict with keys ``pr_ref``, ``head_sha``, and ``intake``.  The
        assembled dict validates against ``merge_readiness.schema.json`` when
        passed to :func:`assess_merge_readiness`.

    Raises
    ------
    ValueError
        If *pr_number* is not a positive integer, *repo* is empty, the runner
        returns malformed JSON, or required fields are absent.
    """
    if not isinstance(pr_number, int) or pr_number < 1:
        raise ValueError(
            f"pr_number must be a positive integer; got {pr_number!r}"
        )
    if not repo or not isinstance(repo, str):
        raise ValueError(f"repo must be a non-empty string; got {repo!r}")

    _run = runner if runner is not None else _default_runner

    # ------------------------------------------------------------------
    # Fetch core PR fields in a single gh invocation
    # ------------------------------------------------------------------
    raw = _run(
        [
            "gh", "pr", "view", str(pr_number),
            "--repo", repo,
            "--json",
            (
                "number,headRefName,baseRefName,headRefOid,"
                "files,commits,reviews,statusCheckRollup,reviewThreads"
            ),
        ]
    )

    try:
        data: dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"gh pr view returned non-JSON output: {exc}\nOutput: {raw[:200]!r}"
        ) from exc

    # ------------------------------------------------------------------
    # Extract and normalise fields
    # ------------------------------------------------------------------
    pr_number_out = data.get("number", pr_number)
    head_ref = data.get("headRefName", "")
    base_ref = data.get("baseRefName", "")
    head_sha: str = data.get("headRefOid", "")

    if not head_sha:
        raise ValueError(
            f"gh pr view returned no headRefOid for PR #{pr_number} in {repo!r}"
        )

    # changed_files: gh returns list of {path, additions, deletions, changeType}
    raw_files = data.get("files", []) or []
    changed_files = [
        f.get("path", "") for f in raw_files if isinstance(f, dict)
    ]

    # commits: gh returns list of {oid, messageHeadline, ...}
    raw_commits = data.get("commits", []) or []
    commits = [
        c.get("oid", "") for c in raw_commits if isinstance(c, dict)
    ]

    # reviews: keep as-is (opaque to generic core)
    reviews = data.get("reviews", []) or []

    # statusCheckRollup: list of {name, conclusion, status, ...}
    raw_checks = data.get("statusCheckRollup", []) or []
    checks = _normalise_checks(raw_checks)

    # reviewThreads: gh returns list of {isResolved, comments, ...}
    raw_threads = data.get("reviewThreads", []) or []
    review_threads = _normalise_threads(raw_threads)

    # Reviewer classifications from reviews
    reviewer_classifications = _classify_reviewers(reviews)

    # Proof refs: not available from raw gh pr view; default to empty
    proof_refs: list[dict] = []
    proof_freshness = "MISSING"

    intake: dict[str, Any] = {
        "intake_completeness": {
            "pr_metadata": "COMPLETE",
            "head_sha": "COMPLETE",
            "changed_files": "COMPLETE",
            "commits": "COMPLETE",
            "reviews": "COMPLETE",
            "review_comments": "MISSING",
            "review_threads": "COMPLETE",
            "issue_comments": "MISSING",
            "checks": "COMPLETE",
            "proof_refs": "MISSING",
            "proof_freshness": "MISSING",
            "reviewer_classifications": "COMPLETE",
            "allowlist": "MISSING",
            "security_release_approval": "MISSING",
        },
        "changed_files": changed_files,
        "commits": commits,
        "checks": checks,
        "reviews": reviews,
        "review_threads": review_threads,
        "reviewer_classifications": reviewer_classifications,
        "unclassified_review_items": [],
        "proof_refs": proof_refs,
        "proof_freshness": proof_freshness,
        "diff_escapes_allowlist": False,
        "security_release_required": False,
        "security_release_approved": False,
    }

    pr_ref = {
        "repo": repo,
        "number": pr_number_out,
        "head_ref": head_ref,
        "base_ref": base_ref,
    }

    return {
        "pr_ref": pr_ref,
        "head_sha": head_sha,
        "intake": intake,
    }


# ---------------------------------------------------------------------------
# Internal normalisers
# ---------------------------------------------------------------------------

def _normalise_checks(raw_checks: list[dict]) -> list[dict]:
    """Normalise ``statusCheckRollup`` entries to the schema check shape.

    stale_to_head is derived from check conclusion only; gh statusCheckRollup is
    semantically head-scoped, so per-check SHA comparison is not attempted (gh does
    not expose a check-run SHA).
    """
    _conclusion_map = {
        "SUCCESS": "SUCCESS",
        "FAILURE": "FAILURE",
        "NEUTRAL": "NEUTRAL",
        "CANCELLED": "NEUTRAL",
        "SKIPPED": "NEUTRAL",
        "TIMED_OUT": "FAILURE",
        "ACTION_REQUIRED": "FAILURE",
        "PENDING": "PENDING",
        "IN_PROGRESS": "PENDING",
        "QUEUED": "PENDING",
        "STALE": "STALE",
    }
    normalised = []
    for raw in raw_checks:
        if not isinstance(raw, dict):
            continue
        name: str = raw.get("name", "") or raw.get("context", "") or ""
        conclusion_raw: str = (raw.get("conclusion") or raw.get("state") or "").upper()
        conclusion = _conclusion_map.get(conclusion_raw, "UNKNOWN")
        stale_to_head = conclusion in {"STALE", "PENDING", "UNKNOWN"}
        normalised.append(
            {
                "name": name,
                "conclusion": conclusion,
                "stale_to_head": stale_to_head,
            }
        )
    return normalised


def _normalise_threads(raw_threads: list[dict]) -> list[dict]:
    """Normalise ``reviewThreads`` to the schema thread shape."""
    normalised = []
    for raw in raw_threads:
        if not isinstance(raw, dict):
            continue
        resolved: bool = bool(raw.get("isResolved", False))
        # gh does not emit a 'blocking' field; classify unresolved as blocking
        blocking: bool = not resolved
        normalised.append({"resolved": resolved, "blocking": blocking})
    return normalised


def _classify_reviewers(reviews: list[dict]) -> list[dict]:
    """Classify reviewer actors from raw review objects.

    GitHub bot login patterns are recognised as KNOWN_BOT; everything else is
    HUMAN unless the actor is absent (UNKNOWN).
    """
    _bot_suffixes = ("[bot]", "-bot", "_bot")
    _known_bots = {
        "github-actions",
        "codecov",
        "dependabot",
        "renovate",
        "google-labs-jules[bot]",
        "copilot-swe-agent[bot]",
    }

    seen: dict[str, str] = {}
    for review in reviews:
        if not isinstance(review, dict):
            continue
        author = review.get("author", {}) or {}
        login: str = (
            author.get("login", "") if isinstance(author, dict) else str(author)
        )
        if not login:
            continue
        if login in seen:
            continue
        if login in _known_bots or any(login.endswith(s) for s in _bot_suffixes):
            kind = "KNOWN_BOT"
        elif login:
            kind = "HUMAN"
        else:
            kind = "UNKNOWN"
        seen[login] = kind

    return [{"actor": actor, "kind": kind} for actor, kind in seen.items()]
