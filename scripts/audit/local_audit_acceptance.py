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
   (with ``report_path`` overridden by the trusted emitter downstream).

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


def _load_schema_enums(schema_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"schema_unreadable: {schema_path}: {exc}"
    if not isinstance(schema, dict):
        return None, f"schema_malformed: {schema_path}"
    return schema, None


def _validate_embedded_audit(
    embedded: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> list[str]:
    """Structural validation against the trusted schema (stdlib only).

    ``report_path`` is intentionally NOT validated here — the trusted emitter
    overrides it with its own canonical artifact path.
    """
    errors: list[str] = []
    properties = schema.get("properties", {})
    required = [key for key in schema.get("required", []) if key != "report_path"]

    for key in required:
        if key not in embedded:
            errors.append(f"local_audit_missing_field: {key}")
    if errors:
        return errors

    status = embedded.get("status")
    status_enum = properties.get("status", {}).get("enum", [])
    if status not in status_enum:
        errors.append(f"local_audit_status_not_in_schema: {status!r}")
    elif status not in PASSING_AUDIT_STATUSES:
        errors.append(f"local_audit_not_passing: {status!r}")

    tool = embedded.get("auditor_tool")
    tool_enum = properties.get("auditor_tool", {}).get("enum", [])
    if tool not in tool_enum:
        errors.append(
            f"local_audit_tool_not_in_schema: {tool!r} (allowed: {sorted(tool_enum)})"
        )
    model = embedded.get("auditor_model")
    model_enum = properties.get("auditor_model", {}).get("enum", [])
    if model not in model_enum:
        errors.append(
            f"local_audit_model_not_in_schema: {model!r} (allowed: {sorted(model_enum)})"
        )

    if embedded.get("required") is not True:
        errors.append("local_audit_required_flag: embedded_audit.required must be true")
    for list_field in ("findings", "fixes_applied", "remaining_risks"):
        if not isinstance(embedded.get(list_field), list):
            errors.append(f"local_audit_field_not_list: {list_field}")
    exit_code = embedded.get("exit_code")
    if exit_code is not None and not isinstance(exit_code, int):
        errors.append("local_audit_exit_code_type: must be integer or null")
    invocation = embedded.get("invocation")
    if invocation is not None and not isinstance(invocation, str):
        errors.append("local_audit_invocation_type: must be string or null")
    return errors


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
    schema, schema_error = _load_schema_enums(schema_path)
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
