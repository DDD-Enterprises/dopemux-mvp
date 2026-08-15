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
3. The signed payload's ``head_sha`` must be the ACTUAL AUDITED COMMIT (the
   commit whose diff a human/AI auditor examined) — not a later "evidence"
   commit that merely adds report artifacts on top. That audited commit must
   be an ancestor of the enforced PR head H, and ``git diff audited..H`` must
   touch ONLY two directories: ``proof/pr_merge/embedded-audit/pr-<N>/`` (the
   signed attestation itself) and ``proof/<PACKET_ID>/`` (the canonical
   packet proof bundle, AGENTS.md section 9.1), where ``PACKET_ID`` is derived
   fail-closed from the signed ``embedded_audit.report_path`` field using the
   trusted schema's own ``report_path`` pattern — never trusted verbatim from
   a separate field an attacker could point anywhere.
4. The local ``embedded_audit`` object must be a passing verdict and must be
   valid against the trusted ``schemas/proof/embedded_audit.schema.json``
   under full Draft 7 semantics — the canonical schema is the single policy
   engine here, so conditional constraints (``allOf``/``if``/``then``),
   ``additionalProperties``, and ``report_path`` are all enforced. A signed
   payload the canonical validator rejects is never accepted, even when a
   downstream trusted emitter would later replace a field of its own.
5. The canonical packet proof bundle named by ``PACKET_ID`` must actually
   exist at the enforced PR head: ``proof/<PACKET_ID>/PROOF.json``, the
   report file named by ``report_path``, and a non-empty
   ``proof/<PACKET_ID>/review_bundle/``. The packet ``PROOF.json`` must
   itself declare the SAME audited commit (``head_sha``) and the SAME
   controlling ``embedded_audit`` verdict/identity (``status``,
   ``auditor_tool``, ``auditor_model``) as the signed PR proof — the two
   proofs must agree, not merely both exist.

This closes a gap where a signed proof could name an "evidence head" (a
commit that only adds report files) as ``head_sha`` instead of the commit an
auditor actually examined: the diff-scope check would then never see the
report-adding commit's own contents, so nothing verified that commit didn't
smuggle in more than "just the report." Binding ``head_sha`` to the true
audited commit removes that blind spot; the packet-directory allowance
still lets the report land in the same delta, but now inside the window the
diff-scope check actually inspects.

Every failure produces ``accepted=false`` with explicit reasons; the caller
(workflow) then falls through to today's SKIPPED/red behaviour. Candidate PR
code is only ever read as git blobs — never checked out or executed.

Trust model (documented, deliberate): a valid signature proves that a holder
of an allow-listed private key attested this exact code was audited. It is an
operator attestation, not an independent third-party audit.

LIMITATION (attested, not proven): the field this module calls ``head_sha`` on
the signed proof — internally ``ATTESTED_AUDITED_SHA`` — is a claim the signer
makes, not a cryptographic binding to an external auditor's actual execution.
This module enforces a real, useful guarantee: every commit between
``ATTESTED_AUDITED_SHA`` and the enforced PR head is restricted to the two
authorized proof trees, so nothing added *after* the attested commit can smuggle
code past this gate. It does NOT and cannot verify that the content actually
present *at* ``ATTESTED_AUDITED_SHA`` is what an auditor genuinely examined —
that still rests entirely on the signer's honesty, same as any operator
attestation. Binding the attested SHA to independently-verifiable evidence of
the auditor's own execution (e.g. auditor-signed output, not producer-signed)
is a separate, harder trust problem and out of scope for this module.
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


def _tree_type(repo_root: Path, rev: str, path: str) -> str | None:
    """Return the git object type of the exact tree entry at ``rev:path``.

    Deliberately exact — ``git ls-tree -r`` matches any path with ``path`` as a
    *prefix* (e.g. a directory ``foo`` incorrectly "containing" ``foo.txt``
    would never trip this, but a *file* accidentally named ``foo`` and a
    *directory* also reachable via a descendant path both need to be told
    apart before callers can require "must be a directory", not "must have
    some descendant somewhere under this string prefix").
    """
    result = _run_git(repo_root, "cat-file", "-t", f"{rev}:{path}")
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "replace").strip()


def _tree_has_entries(repo_root: Path, rev: str, path: str) -> bool:
    """True if ``path`` is a directory (git tree) at ``rev`` with >=1 real blob.

    Deliberately checks each recursive entry's OWN object type, not just that
    ``ls-tree`` printed a line under this path: a gitlink/submodule entry
    (object type ``commit``) is a pointer to another repository's history,
    not in-repo evidence, but a bare name-only listing would print its path
    just like a real file and satisfy a presence-only check.
    """
    if _tree_type(repo_root, rev, path) != "tree":
        return False
    result = _run_git(repo_root, "ls-tree", "-r", rev, "--", path)
    if result.returncode != 0:
        return False
    for line in result.stdout.decode("utf-8", "replace").splitlines():
        # ls-tree line format: "<mode> <type> <sha>\t<path>"
        fields = line.split("\t", 1)[0].split()
        if len(fields) >= 2 and fields[1] == "blob":
            return True
    return False


def _extract_packet_id(report_path: str, schema: Mapping[str, Any]) -> str | None:
    """Derive PACKET_ID from a schema-valid ``report_path``.

    Deliberately re-reads the pattern from the trusted schema itself rather
    than hard-coding a parallel regex, so a ``report_path`` this rejects is
    exactly one the canonical validator would also reject. The schema's own
    capture groups are around the optional ``_REPAIR_N`` suffix, not the
    packet segment, so once the whole-string pattern match confirms the
    fixed three-segment shape (``proof/<packet_id>/AUDITOR..._REPORT.md``),
    the packet segment is taken by position, not by group. Returns ``None``
    if the schema has no usable pattern or the string does not match it.
    """
    pattern = schema.get("properties", {}).get("report_path", {}).get("pattern")
    if not isinstance(pattern, str):
        return None
    if re.match(pattern, report_path) is None:
        return None
    segments = report_path.split("/")
    if len(segments) != 3 or segments[0] != "proof" or not segments[1]:
        return None
    return segments[1]


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

    The trusted schema describes CI-emitted diagnostic proofs as well as
    attestations, so it is deliberately more permissive than acceptance:

    * it permits non-passing verdicts (``FAIL``, ``SKIPPED``);
    * it types ``required`` as a plain boolean, so ``required: false`` is
      schema-valid.

    Local attestation accepts neither. ``required: false`` matters because a
    downstream emitter promotes an accepted attestation to ``executed: true``
    while final enforcement checks the verdict and not this flag — so accepting
    it would let the mandatory embedded-audit gate go green for a proof that
    declares the audit was not required.

    Every gate here is one the schema cannot express. Adding a schema check must
    never remove one of them.
    """
    errors: list[str] = []
    status = embedded.get("status")
    if status not in PASSING_AUDIT_STATUSES:
        errors.append(f"local_audit_not_passing: {status!r}")
    if embedded.get("required") is not True:
        errors.append("local_audit_required_flag: embedded_audit.required must be true")
    return errors


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
        "packet_id": None,
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

    # ATTESTED_AUDITED_SHA (see module LIMITATION docstring): the signer's
    # claim of which commit was audited, not an independently-verified fact.
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

    # embedded_audit must be validated BEFORE the diff-scope check: the
    # packet-directory allowance in that check is derived from report_path,
    # which only exists once the object is schema-valid.
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

    report_path = str(embedded.get("report_path") or "")
    packet_id = _extract_packet_id(report_path, schema)
    if packet_id is None:
        reasons.append(
            f"packet_id_undecidable: report_path {report_path!r} did not yield a "
            "PACKET_ID under the trusted schema's report_path pattern"
        )
        return attestation
    packet_dir = f"proof/{packet_id}"
    attestation["packet_id"] = packet_id

    changed = _changed_paths(repo_root, audited_sha, head_sha)
    if changed is None:
        reasons.append("delta_unavailable: git diff between audited and head failed")
        return attestation
    allowed_prefixes = (f"{proof_dir}/", f"{packet_dir}/")
    offending = [path for path in changed if not path.startswith(allowed_prefixes)]
    if offending:
        preview = ", ".join(sorted(offending)[:5])
        reasons.append(
            "delta_touches_code: commits after the audited SHA modify paths outside "
            f"{proof_dir}/ and {packet_dir}/ ({preview})"
        )
        return attestation

    # The canonical packet proof bundle (AGENTS.md section 9.1) must actually exist
    # at the enforced PR head, and must agree with the signed PR proof on the
    # audited commit and the controlling verdict/identity — two proofs that
    # merely coexist without agreeing would let one attest what the other
    # never examined.
    packet_proof_path = f"{packet_dir}/PROOF.json"
    packet_proof_bytes = _read_blob(repo_root, head_sha, packet_proof_path)
    if packet_proof_bytes is None:
        reasons.append(f"packet_proof_absent: {packet_proof_path} not present at PR head")
        return attestation
    if _tree_type(repo_root, head_sha, report_path) != "blob":
        reasons.append(
            f"packet_report_absent: {report_path} is not a file (blob) at PR head"
        )
        return attestation
    review_bundle_dir = f"{packet_dir}/review_bundle"
    if not _tree_has_entries(repo_root, head_sha, review_bundle_dir):
        reasons.append(
            f"packet_review_bundle_missing_or_empty: {review_bundle_dir}/ not present "
            "or empty at PR head"
        )
        return attestation

    try:
        packet_proof = json.loads(packet_proof_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        reasons.append(f"packet_proof_malformed: {exc}")
        return attestation
    if not isinstance(packet_proof, dict):
        reasons.append("packet_proof_malformed: root is not an object")
        return attestation

    packet_audited_sha = str(packet_proof.get("head_sha") or "")
    if packet_audited_sha != audited_sha:
        reasons.append(
            "packet_proof_head_sha_mismatch: packet PROOF.json head_sha "
            f"{packet_audited_sha!r} does not agree with signed PR proof's "
            f"audited head_sha {audited_sha!r}"
        )
        return attestation

    # packet_proof lives at proof/<packet_id>/PROOF.json purely by path
    # convention; nothing above enforces that ITS OWN declared packet_id
    # agrees with the directory it was read from / the PACKET_ID the signed
    # report_path derived. Without this, a stale or misdirected bundle whose
    # internal packet_id names something else could still satisfy every
    # other check by sheer path placement.
    packet_declared_id = packet_proof.get("packet_id")
    if packet_declared_id != packet_id:
        reasons.append(
            "packet_proof_packet_id_mismatch: packet PROOF.json packet_id "
            f"{packet_declared_id!r} does not match PACKET_ID {packet_id!r} "
            "derived from the signed report_path"
        )
        return attestation

    packet_embedded = packet_proof.get("embedded_audit")
    if not isinstance(packet_embedded, dict):
        reasons.append("packet_proof_embedded_audit_missing: embedded_audit object required")
        return attestation
    packet_schema_errors = _validate_embedded_audit(packet_embedded, schema)
    if packet_schema_errors:
        reasons.extend(f"packet_proof_{err}" for err in packet_schema_errors)
        return attestation

    identity_fields = ("status", "auditor_tool", "auditor_model")
    mismatched = [
        field
        for field in identity_fields
        if packet_embedded.get(field) != embedded.get(field)
    ]
    if mismatched:
        reasons.append(
            "packet_proof_verdict_identity_mismatch: packet PROOF.json disagrees with "
            f"signed PR proof on {', '.join(mismatched)}"
        )
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
