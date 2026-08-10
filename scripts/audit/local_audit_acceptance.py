#!/usr/bin/env python3
"""Fail-closed acceptance of locally-run, ssh-signed embedded-audit proofs.

Purpose
-------
The trusted embedded-audit workflow cannot execute an auditor CLI when no
provider credentials are provisioned. This module lets the trusted workflow
accept an audit that was executed *locally* (pr-merge/steward flow), under a
strict, fail-closed contract:

1. The PR branch carries ``proof/pr_merge/embedded-audit/pr-<N>/PROOF.json``
   plus a detached OpenSSH signature ``PROOF.json.sig`` over those exact bytes
   (``ssh-keygen -Y sign -n dopemux-embedded-audit``).
2. The signature must verify against the allowed-signers file taken from the
   TRUSTED ref (never from the PR branch).
3. The signed payload must name this repo and this PR number, and its
   ``head_sha`` (the audited commit A) must be an ancestor of the enforced PR
   head H where ``git diff A..H`` touches ONLY the proof directory itself
   (exact-head, proof-only delta — committing the proof is the sole change
   allowed on top of the audited code).
4. The local ``embedded_audit`` object must be a passing verdict and must be
   valid against the trusted ``schemas/proof/embedded_audit.schema.json``
   under full Draft 7 semantics — the canonical schema is the single policy
   engine here, so conditional constraints (``allOf``/``if``/``then``),
   ``additionalProperties``, and ``report_path`` are all enforced. A signed
   payload the canonical validator rejects is never accepted, even when a
   downstream trusted emitter would later replace a field of its own.

Every failure produces ``accepted=false`` with explicit reasons; the caller
(workflow) then falls through to today's SKIPPED/red behaviour. Candidate PR
code is only ever read as git blobs — never checked out or executed.

Trust model (documented, deliberate): a valid signature proves that a holder
of an allow-listed private key attested this exact code was audited. It is an
operator attestation, not an independent third-party audit.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

try:  # Canonical schema engine. Absence must fail closed, never fall back.
    from jsonschema import Draft7Validator
    from jsonschema.exceptions import SchemaError
except ImportError as _exc:  # pragma: no cover - exercised via monkeypatch
    Draft7Validator = None  # type: ignore[assignment]
    SchemaError = None  # type: ignore[assignment]
    JSONSCHEMA_IMPORT_ERROR: str | None = str(_exc)
else:
    JSONSCHEMA_IMPORT_ERROR = None

SIGNATURE_NAMESPACE = "dopemux-embedded-audit"
DEFAULT_ALLOWED_SIGNERS = Path("config/audit/embedded-audit-allowed-signers")
DEFAULT_SCHEMA_PATH = Path("schemas/proof/embedded_audit.schema.json")
PROOF_DIR_TEMPLATE = "proof/pr_merge/embedded-audit/pr-{pr_number}"
PASSING_AUDIT_STATUSES = frozenset({"PASS", "PASS_WITH_RISKS"})
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Deepen in two bounded steps; beyond this the proof commit is suspiciously far
# from the audited commit and we fail closed rather than fetch unbounded history.
FETCH_DEPTHS = (100, 500)


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        check=False,
    )


def _read_blob(repo_root: Path, rev: str, path: str) -> bytes | None:
    result = _run_git(repo_root, "cat-file", "blob", f"{rev}:{path}")
    if result.returncode != 0:
        return None
    return result.stdout


def _object_exists(repo_root: Path, sha: str) -> bool:
    return _run_git(repo_root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def _ensure_objects(repo_root: Path, head_sha: str, audited_sha: str) -> str | None:
    """Fetch enough history for the ancestry/diff checks. Returns error or None."""
    if _object_exists(repo_root, head_sha) and _object_exists(repo_root, audited_sha):
        return None
    for depth in FETCH_DEPTHS:
        _run_git(
            repo_root,
            "fetch",
            "--no-tags",
            f"--depth={depth}",
            "origin",
            head_sha,
        )
        if _object_exists(repo_root, head_sha) and _object_exists(repo_root, audited_sha):
            return None
    return (
        f"objects_unreachable: audited commit {audited_sha} not reachable from "
        f"head {head_sha} within fetch depth {FETCH_DEPTHS[-1]}"
    )


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    return (
        _run_git(repo_root, "merge-base", "--is-ancestor", ancestor, descendant).returncode
        == 0
    )


def _changed_paths(repo_root: Path, base: str, head: str) -> list[str] | None:
    # --no-renames: porcelain diff detects renames by default (diff.renames),
    # and a rename's --name-only output can show only the destination path — a
    # rename of a code file INTO the proof dir would otherwise hide the source
    # deletion from the proof-only-delta check.
    result = _run_git(repo_root, "diff", "--no-renames", "--name-only", base, head)
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.decode("utf-8", "replace").splitlines() if line]


def _verify_signature(
    proof_bytes: bytes,
    signature_bytes: bytes,
    allowed_signers: Path,
) -> tuple[str | None, str | None]:
    """Verify an OpenSSH detached signature. Returns (principal, error)."""
    if not allowed_signers.is_file():
        return None, f"allowed_signers_missing: {allowed_signers}"
    with tempfile.TemporaryDirectory(prefix="local-audit-sig.") as tmp:
        sig_path = Path(tmp) / "PROOF.json.sig"
        sig_path.write_bytes(signature_bytes)

        find = subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "find-principals",
                "-s",
                str(sig_path),
                "-f",
                str(allowed_signers),
            ],
            capture_output=True,
            check=False,
        )
        if find.returncode != 0:
            detail = find.stderr.decode("utf-8", "replace").strip()
            return None, f"signature_principal_not_allowed: {detail or 'no matching principal'}"
        principals = [
            line.strip()
            for line in find.stdout.decode("utf-8", "replace").splitlines()
            if line.strip()
        ]
        if not principals:
            return None, "signature_principal_not_allowed: empty principal list"
        principal = principals[0]

        verify = subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "verify",
                "-f",
                str(allowed_signers),
                "-I",
                principal,
                "-n",
                SIGNATURE_NAMESPACE,
                "-s",
                str(sig_path),
            ],
            input=proof_bytes,
            capture_output=True,
            check=False,
        )
        if verify.returncode != 0:
            detail = verify.stderr.decode("utf-8", "replace").strip()
            return None, f"signature_invalid: {detail or 'verification failed'}"
    return principal, None


def _load_trusted_schema(schema_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"schema_unreadable: {schema_path}: {exc}"
    if not isinstance(schema, dict):
        return None, f"schema_malformed: {schema_path}"
    return schema, None


def _pointer(error: Any) -> str:
    """JSON Pointer for a validation error, ``<root>`` for the object itself."""
    parts = [str(part) for part in error.absolute_path]
    return "/" + "/".join(parts) if parts else "<root>"


def schema_validation_errors(
    embedded: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> list[str]:
    """Validate ``embedded_audit`` against the trusted schema, Draft 7 semantics.

    The canonical schema is the single policy engine: conditional constraints
    are executed by the real validator rather than mirrored by hand, so a
    conditional added to the schema is enforced here the day it lands. This is
    deliberately the *whole* object — ``report_path`` included. A previous
    hand-rolled implementation skipped ``allOf`` entirely and exempted
    ``report_path``, which let a signed payload the canonical validator rejects
    be accepted here (see ``tests/audit/test_local_audit_acceptance.py``).

    Returns schema errors only. Verdict policy is applied separately by
    :func:`policy_errors` — the schema admits ``FAIL``/``SKIPPED``, acceptance
    does not.
    """
    if Draft7Validator is None:
        return [
            "schema_validator_unavailable: jsonschema is required to validate the "
            f"signed embedded_audit against the trusted schema ({JSONSCHEMA_IMPORT_ERROR})"
        ]
    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as exc:  # type: ignore[misc]
        return [f"schema_malformed: trusted schema is not valid Draft 7: {exc.message}"]

    errors = sorted(
        Draft7Validator(schema).iter_errors(embedded),
        key=lambda err: (list(err.absolute_path), err.message),
    )
    return [
        f"local_audit_schema_invalid: {_pointer(err)}: {err.message}" for err in errors
    ]


def policy_errors(embedded: Mapping[str, Any]) -> list[str]:
    """Acceptance policy that is not a JSON Schema concern.

    The trusted schema permits non-passing verdicts because it also describes
    CI-emitted diagnostic proofs. Local attestation accepts passing verdicts
    only.
    """
    status = embedded.get("status")
    if status not in PASSING_AUDIT_STATUSES:
        return [f"local_audit_not_passing: {status!r}"]
    return []


def _validate_embedded_audit(
    embedded: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> list[str]:
    """Canonical-schema validation followed by acceptance policy."""
    errors = schema_validation_errors(embedded, schema)
    if errors:
        return errors
    return policy_errors(embedded)


def evaluate_local_audit(
    *,
    repo_root: Path,
    repo: str,
    pr_number: int,
    head_sha: str,
    allowed_signers: Path,
    schema_path: Path,
) -> dict[str, Any]:
    """Evaluate a signed local audit proof for exactly this PR head.

    Returns an attestation record; ``accepted`` is True only when every check
    passed. All git access is read-only blob/commit inspection.
    """
    proof_dir = PROOF_DIR_TEMPLATE.format(pr_number=pr_number)
    proof_path = f"{proof_dir}/PROOF.json"
    signature_path = f"{proof_path}.sig"
    attestation: dict[str, Any] = {
        "accepted": False,
        "reasons": [],
        "repo": repo,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "audited_sha": None,
        "principal": None,
        "proof_path": proof_path,
        "signature_namespace": SIGNATURE_NAMESPACE,
        "embedded_audit": None,
    }
    reasons: list[str] = attestation["reasons"]

    if not _SHA_RE.match(head_sha):
        reasons.append(f"head_sha_malformed: {head_sha!r}")
        return attestation
    if not _object_exists(repo_root, head_sha):
        _run_git(repo_root, "fetch", "--no-tags", f"--depth={FETCH_DEPTHS[0]}", "origin", head_sha)
    if not _object_exists(repo_root, head_sha):
        reasons.append(f"head_unreachable: {head_sha}")
        return attestation

    proof_bytes = _read_blob(repo_root, head_sha, proof_path)
    if proof_bytes is None:
        reasons.append(f"local_proof_absent: {proof_path} not present at PR head")
        return attestation
    signature_bytes = _read_blob(repo_root, head_sha, signature_path)
    if signature_bytes is None:
        reasons.append(f"local_signature_absent: {signature_path} not present at PR head")
        return attestation

    principal, sig_error = _verify_signature(proof_bytes, signature_bytes, allowed_signers)
    if sig_error:
        reasons.append(sig_error)
        return attestation
    attestation["principal"] = principal

    try:
        proof = json.loads(proof_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        reasons.append(f"local_proof_malformed: {exc}")
        return attestation
    if not isinstance(proof, dict):
        reasons.append("local_proof_malformed: root is not an object")
        return attestation

    proof_repo = str(proof.get("repo") or "")
    if proof_repo != repo:
        reasons.append(f"local_proof_repo_mismatch: {proof_repo!r} expected {repo!r}")
    try:
        proof_pr = int(proof.get("pr_number"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        proof_pr = None
    if proof_pr != pr_number:
        reasons.append(
            f"local_proof_pr_mismatch: {proof.get('pr_number')!r} expected {pr_number}"
        )

    audited_sha = str(proof.get("head_sha") or "")
    if not _SHA_RE.match(audited_sha):
        reasons.append(f"local_proof_audited_sha_malformed: {audited_sha!r}")
        return attestation
    attestation["audited_sha"] = audited_sha
    if reasons:
        return attestation

    fetch_error = _ensure_objects(repo_root, head_sha, audited_sha)
    if fetch_error:
        reasons.append(fetch_error)
        return attestation
    if not _is_ancestor(repo_root, audited_sha, head_sha):
        reasons.append(
            f"audited_sha_not_ancestor: {audited_sha} is not an ancestor of {head_sha}"
        )
        return attestation

    changed = _changed_paths(repo_root, audited_sha, head_sha)
    if changed is None:
        reasons.append("delta_unavailable: git diff between audited and head failed")
        return attestation
    offending = [path for path in changed if not path.startswith(f"{proof_dir}/")]
    if offending:
        preview = ", ".join(sorted(offending)[:5])
        reasons.append(
            "delta_touches_code: commits after the audited SHA modify paths outside "
            f"{proof_dir}/ ({preview})"
        )
        return attestation

    embedded = proof.get("embedded_audit")
    if not isinstance(embedded, dict):
        reasons.append("local_audit_missing: embedded_audit object required")
        return attestation
    schema, schema_error = _load_trusted_schema(schema_path)
    if schema is None:
        reasons.append(schema_error or f"schema_unreadable: {schema_path}")
        return attestation
    schema_errors = _validate_embedded_audit(embedded, schema)
    if schema_errors:
        reasons.extend(schema_errors)
        return attestation

    attestation["embedded_audit"] = embedded
    attestation["accepted"] = True
    return attestation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a signed local embedded-audit proof committed on a PR branch "
            "(fail-closed; trusted-ref allowed-signers only)."
        )
    )
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--allowed-signers", type=Path, default=DEFAULT_ALLOWED_SIGNERS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--out", required=True, type=Path, help="Attestation JSON output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    attestation = evaluate_local_audit(
        repo_root=args.repo_root,
        repo=args.repo,
        pr_number=args.pr,
        head_sha=args.head_sha,
        allowed_signers=args.allowed_signers,
        schema_path=args.schema,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if attestation["accepted"]:
        print(
            f"local audit attestation ACCEPTED for PR {args.pr} "
            f"(principal={attestation['principal']}, audited={attestation['audited_sha']})"
        )
        return 0
    print(
        "local audit attestation REJECTED: " + "; ".join(attestation["reasons"]),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
