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
    AND the A..H delta is confined to paths within the immutable
        proof-evidence namespace (rooted at "proof/") that are also
        declared by the proof itself (its own committed path, or a
        report_path it names) -- see ``_is_safe_proof_namespace_path`` and
        ``allowed_successor_paths``.

A successor commit's own proof payload -- including any ``report_path`` it
declares -- is untrusted content controlled by that same commit; it is
never sufficient on its own to widen the allowed delta. A candidate path is
only admitted after independently proving it lives inside the proof
namespace, so a successor can never smuggle a code change past the
proof-only check by relabelling it as "the report".

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

# Every path admitted into allowed_successor_paths() must be rooted here.
# This is the "immutable proof-evidence namespace": a successor commit's
# own proof payload is untrusted (it fully controls that payload's
# content), so any path *named inside* that payload -- e.g. report_path --
# must still be independently confined to this namespace before it is
# trusted, or a successor could smuggle a code change past the proof-only
# check by simply relabelling it as "the report".
_PROOF_NAMESPACE_ROOT = "proof"

# Redundant with the proof/-root requirement today (anything rooted at
# "proof" cannot also start with these prefixes), kept as explicit defense
# in depth against a future relaxation of _PROOF_NAMESPACE_ROOT.
_DENIED_PATH_PREFIXES = ("src/", ".github/", "tools/", "tests/")


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


def _is_safe_proof_namespace_path(path: object) -> bool:
    """Fail-closed structural check that ``path`` names a file confined to
    the immutable proof-evidence namespace (``_PROOF_NAMESPACE_ROOT``).

    Rejects: non-strings/empty strings, absolute paths, backslashes,
    empty/``.``/``..`` path components (traversal), and anything not rooted
    at ``proof/``. This is applied to every candidate path admitted into
    ``allowed_successor_paths`` -- including a caller-supplied
    ``proof_path`` and any ``report_path`` declared inside the proof
    payload -- so a path cannot be trusted merely because it appears
    somewhere in already-bound data; it must independently prove it lives
    in the proof namespace.
    """
    if not isinstance(path, str) or not path:
        return False
    if path.startswith("/") or path.startswith("\\") or "\\" in path:
        return False
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    if parts[0] != _PROOF_NAMESPACE_ROOT:
        return False
    if any(path.startswith(prefix) for prefix in _DENIED_PATH_PREFIXES):
        return False
    return True


def allowed_successor_paths(
    proof_path: str, proof_payload: Mapping[str, Any]
) -> set[str]:
    """Narrow allow-list confined to the immutable proof-evidence namespace.

    Deliberately NOT "anything under proof/" as a glob -- exactly the
    committed proof file path (as supplied by the caller, e.g. the
    workflow_dispatch ``proof_path`` input), plus the proof's own declared
    report path (``embedded_audit.report_path``) when present. Neither is
    trusted merely for appearing in already-bound data: both must
    independently satisfy ``_is_safe_proof_namespace_path`` before being
    admitted. This matters most for ``report_path``, which is read from the
    proof payload as it exists wherever the caller loaded it from -- for a
    successor commit that is fully attacker-controlled content in that same
    commit, not data verified at an earlier, already-audited commit (the
    proof file legitimately may not even exist at the audited commit A, so
    there is nothing at A to re-fetch it from). A ``report_path`` that
    fails the namespace check is simply never added to the allow-list --
    it is NOT treated as a hard verification failure, since it may be
    unused filler in an otherwise-legitimate proof. If a successor's diff
    actually touches that path, it will then correctly show up as a
    disallowed path in ``verify_proof_successor``.
    """
    allowed: set[str] = set()
    if _is_safe_proof_namespace_path(proof_path):
        allowed.add(proof_path)
    embedded = proof_payload.get("embedded_audit") if isinstance(proof_payload, Mapping) else None
    if isinstance(embedded, Mapping):
        report_path = embedded.get("report_path")
        if _is_safe_proof_namespace_path(report_path):
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
    if not _is_safe_proof_namespace_path(proof_path):
        return False, [f"proof_path_invalid: {proof_path!r} is outside the proof namespace"]

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
