"""Successor-aware acceptance for committed embedded-audit proofs.

The packaged embedded-audit template (``dopemux init``) and the packaged
``dopemux_pr_steward`` CLI historically required a committed proof's
``head_sha`` to equal the live PR head exactly. That is correct for the
common case (the proof was generated at the exact commit under review) but
rejects a deliberate, narrower pattern this repository's own governance uses:
an audited content commit ``A`` followed by one or more later commits that
add ONLY proof evidence (canonical proof bundle, signature, report) on top,
without touching audited content again. Under that pattern the live PR head
``H`` legitimately differs from the proof's own ``head_sha`` (``A``).

This module distinguishes:

    A = the audited content commit (``proof.head_sha``)
    H = the live PR head

and accepts either ``A == H`` (the legacy/simple case) or:

    A is an ancestor of H
    AND the A..H delta is confined to the proof's own declared paths

It never rewrites or reinterprets ``head_sha`` to mean anything other than
"the commit actually audited" -- callers that need the live head continue to
bind it separately (e.g. status publication, settlement checks).

Mirrors the bounded-depth-fetch + ``git merge-base --is-ancestor`` + exact
tree-diff approach in ``scripts/audit/local_audit_acceptance.py`` (this
repository's own signed-proof acceptance engine), but is deliberately
self-contained: installed downstream repositories (``dopemux init``
consumers) do not carry ``scripts/audit`` in the packaged wheel, so this
module has no dependency on it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Deepen in two bounded steps; beyond this the proof commit is suspiciously
# far from the live head and we fail closed rather than fetch unbounded
# history. Matches scripts/audit/local_audit_acceptance.py's FETCH_DEPTHS.
FETCH_DEPTHS = (100, 500)

DEFAULT_PROOF_PATH = "proof/PROOF.json"


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        check=False,
    )


def _object_exists(repo_root: Path, sha: str) -> bool:
    return _run_git(repo_root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def _ensure_objects(repo_root: Path, live_head_sha: str, audited_head_sha: str) -> str | None:
    """Fetch enough history for the ancestry/diff checks. Returns error or None."""
    if _object_exists(repo_root, live_head_sha) and _object_exists(repo_root, audited_head_sha):
        return None
    for depth in FETCH_DEPTHS:
        _run_git(
            repo_root,
            "fetch",
            "--no-tags",
            f"--depth={depth}",
            "origin",
            live_head_sha,
        )
        if _object_exists(repo_root, live_head_sha) and _object_exists(repo_root, audited_head_sha):
            return None
    return (
        f"objects_unreachable: audited commit {audited_head_sha} not reachable "
        f"from live head {live_head_sha} within fetch depth {FETCH_DEPTHS[-1]}"
    )


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    return (
        _run_git(repo_root, "merge-base", "--is-ancestor", ancestor, descendant).returncode
        == 0
    )


def _changed_paths(repo_root: Path, base: str, head: str) -> list[str] | None:
    # --no-renames: a rename's --name-only output can show only the
    # destination path, which would hide a source deletion from the
    # proof-only-delta check if the rename moved a code file into an
    # allowed path.
    result = _run_git(repo_root, "diff", "--no-renames", "--name-only", base, head)
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.decode("utf-8", "replace").splitlines() if line]


def allowed_successor_paths(
    proof_path: str, proof_payload: Mapping[str, Any]
) -> set[str]:
    """Narrow allow-list derived only from data already bound to this proof.

    Deliberately NOT "anything under proof/" -- exactly the exact committed
    proof file path (as supplied by the caller, e.g. the workflow_dispatch
    ``proof_path`` input), plus the proof's own declared report path
    (``embedded_audit.report_path``) when present. Both are attacker-
    uncontrollable in context: ``proof_path`` is validated upstream (a
    workflow input matched against a strict path regex before this module
    ever runs), and ``report_path`` is read from the proof JSON blob at the
    already-verified audited commit, not from the untrusted live head.
    """
    allowed = {proof_path}
    embedded = proof_payload.get("embedded_audit") if isinstance(proof_payload, Mapping) else None
    if isinstance(embedded, Mapping):
        report_path = embedded.get("report_path")
        if isinstance(report_path, str) and report_path:
            allowed.add(report_path)
    return allowed


def verify_proof_successor(
    repo_root: Path,
    *,
    live_head_sha: str,
    audited_head_sha: str,
    proof_path: str = DEFAULT_PROOF_PATH,
    proof_payload: Mapping[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Return ``(ok, reasons)`` for a proof whose ``head_sha`` may lag the
    live PR head under the proof-only-successor convention.

    ``ok`` is True when ``audited_head_sha == live_head_sha`` (the legacy
    case) or when ``audited_head_sha`` is a verified ancestor of
    ``live_head_sha`` with the intervening delta confined to
    ``allowed_successor_paths``. Fails closed (``ok=False``) on any
    malformed input, unreachable git objects, non-ancestry, or any path in
    the delta outside the allow-list -- never guesses PASS.
    """
    reasons: list[str] = []
    if not _SHA_RE.fullmatch(live_head_sha or ""):
        return False, ["live_head_sha_invalid"]
    if not _SHA_RE.fullmatch(audited_head_sha or ""):
        return False, ["audited_head_sha_invalid"]
    if audited_head_sha == live_head_sha:
        return True, []

    err = _ensure_objects(repo_root, live_head_sha, audited_head_sha)
    if err:
        return False, [err]

    if not _is_ancestor(repo_root, audited_head_sha, live_head_sha):
        return False, [
            f"audited_head_not_ancestor: {audited_head_sha} is not an ancestor "
            f"of live head {live_head_sha}"
        ]

    changed = _changed_paths(repo_root, audited_head_sha, live_head_sha)
    if changed is None:
        return False, ["successor_diff_failed"]

    allowed = allowed_successor_paths(proof_path, proof_payload or {})
    disallowed = [path for path in changed if path not in allowed]
    if disallowed:
        return False, [
            "successor_delta_not_proof_only: " + ", ".join(sorted(disallowed))
        ]

    return True, reasons
