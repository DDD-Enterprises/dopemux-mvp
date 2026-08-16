#!/bin/bash
#
# Sign a locally-produced embedded-audit proof so the trusted embedded-audit
# workflow can accept it (see scripts/audit/local_audit_acceptance.py).
#
# Usage:
#   scripts/audit/sign_local_audit_proof.sh <pr-number> [signing-key]
#
# Prerequisites:
#   - proof/pr_merge/embedded-audit/pr-<N>/PROOF.json exists, with:
#       repo, pr_number, head_sha (the audited commit), and a PASSING,
#       schema-valid embedded_audit object (auditor_tool/auditor_model must be
#       values from schemas/proof/embedded_audit.schema.json).
#   - The canonical AGENTS.md 9.1 packet proof bundle (proof/<PACKET_ID>/
#     {PROOF.json,<report>,review_bundle/}) is ALREADY COMMITTED (as its own
#     proof-only successor commit) before running this script -- the
#     trusted acceptance engine reads it from committed git blobs at the
#     final PR head, never the working tree, so this script fails closed if
#     that directory has any uncommitted changes.
#   - Your PUBLIC key is listed in config/audit/embedded-audit-allowed-signers
#     on main (one-time setup; instructions in that file).
#
# After signing, commit BOTH files to the PR branch. That commit must be the
# only change on top of the audited head_sha (proof-only delta), or CI rejects.
#
set -euo pipefail

PR_NUMBER="${1:?usage: sign_local_audit_proof.sh <pr-number> [signing-key]}"
KEY_PATH="${2:-$HOME/.ssh/dopemux_audit_signing}"
NAMESPACE="dopemux-embedded-audit"
PROOF_DIR="proof/pr_merge/embedded-audit/pr-${PR_NUMBER}"
PROOF_FILE="${PROOF_DIR}/PROOF.json"

if [ ! -f "$PROOF_FILE" ]; then
    echo "error: $PROOF_FILE not found (run the local audit flow first)" >&2
    exit 1
fi
if [ ! -f "$KEY_PATH" ]; then
    echo "error: signing key $KEY_PATH not found" >&2
    echo "one-time setup: ssh-keygen -t ed25519 -N '' -f $KEY_PATH" >&2
    exit 1
fi

# Pre-flight the proof shape locally so rejections surface here, not in CI.
# Imports the SAME schema_validation_errors/policy_errors the trusted
# acceptance engine runs (scripts/audit/local_audit_acceptance.py), rather
# than hand-mirroring a subset of its checks -- a packet embedded_audit
# object that agrees on status/auditor_tool/auditor_model but fails schema
# or policy elsewhere (required:false, missing invocation, etc.) must not be
# signed as "proof shape OK" only to be rejected later by CI's full check.
python3 - "$PROOF_FILE" "$PR_NUMBER" <<'PY'
import json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts.audit.local_audit_acceptance import (
    _extract_packet_id,
    policy_errors,
    schema_validation_errors,
)


def _git_dirty(path: Path) -> list[str]:
    """Uncommitted (untracked/modified/staged) changes under ``path``.

    The trusted acceptance engine reads the packet bundle from committed git
    BLOBS at the final PR head -- never the working tree. A filesystem-only
    preflight (Path.is_file()/is_dir()/rglob()) can report "OK" for a bundle
    that exists on disk but was never actually committed, or was modified
    after the last commit; CI would then see a stale or absent bundle and
    reject with packet_proof_absent/packet_report_absent/etc. even though
    signing "succeeded" locally.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", str(path)],
        capture_output=True, text=True, check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]

proof_file, pr_number = Path(sys.argv[1]), int(sys.argv[2])
proof = json.loads(proof_file.read_text(encoding="utf-8"))
errors = []
if int(proof.get("pr_number") or 0) != pr_number:
    errors.append(f"pr_number={proof.get('pr_number')!r} != {pr_number}")
if not proof.get("repo"):
    errors.append("repo missing")
if not re.match(r"^[0-9a-f]{40}$", str(proof.get("head_sha") or "")):
    errors.append("head_sha missing or not a full 40-char sha")

schema_path = Path("schemas/proof/embedded_audit.schema.json")
schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.is_file() else None
embedded = proof.get("embedded_audit") or {}
if schema is None:
    errors.append(f"schema_unreadable: {schema_path}")
else:
    errors.extend(f"embedded_audit.{e}" for e in schema_validation_errors(embedded, schema))
    errors.extend(f"embedded_audit.{e}" for e in policy_errors(embedded))

# Mirror local_audit_acceptance.py's canonical packet-bundle gate (AGENTS.md
# 9.1) here too, so a mismatched/missing bundle fails at signing time, not
# only after CI runs the real check against the pushed commit. Reuses the
# ACTUAL _extract_packet_id -- not a re-implemented parallel derivation --
# so this can never independently drift out of sync with what the trusted
# acceptance engine accepts (e.g. by forgetting the reserved-namespace
# rejection when that gets added there).
report_path = str(embedded.get("report_path") or "")
packet_id = _extract_packet_id(report_path, schema) if schema is not None else None
if packet_id is None:
    errors.append(f"embedded_audit.report_path={report_path!r} does not yield a PACKET_ID")
else:
    packet_dir = Path("proof") / packet_id
    packet_proof_path = packet_dir / "PROOF.json"
    report_file = Path(report_path)
    review_bundle_dir = packet_dir / "review_bundle"
    # is_symlink() only inspects the FINAL path component -- it says nothing
    # about ANCESTOR directories. A symlinked packet_dir itself (proof/
    # <PACKET_ID> pointing elsewhere) would make report_file.is_symlink(),
    # review_bundle_dir.is_symlink(), and packet_proof_path.is_symlink()
    # ALL return False (each only checks the leaf at the resolved location),
    # silently bypassing every leaf-level symlink check below. Guard once,
    # up front, and skip every downstream packet_dir-based check on failure
    # rather than threading the same condition through each one.
    packet_dir_ok = not packet_dir.is_symlink()
    if not packet_dir_ok:
        errors.append(f"{packet_dir}/ is a symlink, not a real directory")

    # Explicit is_symlink() checks: Path.is_file()/is_dir() FOLLOW symlinks,
    # so a symlinked report file or a review_bundle/ that is itself a
    # symlink would otherwise pass here even though the eventual committed
    # blob has mode 120000 and the trusted acceptance engine rejects it.
    if packet_dir_ok and (report_file.is_symlink() or not report_file.is_file()):
        errors.append(f"{report_path} is not a regular file (symlink or absent)")
    if packet_dir_ok and (review_bundle_dir.is_symlink() or not review_bundle_dir.is_dir()):
        errors.append(f"{review_bundle_dir}/ is not a real directory (symlink or absent)")
    elif packet_dir_ok and not any(
        p.is_file() and not p.is_symlink() for p in review_bundle_dir.rglob("*")
    ):
        errors.append(f"{review_bundle_dir}/ missing or empty (no real file entries)")
    if packet_dir_ok:
        dirty = _git_dirty(packet_dir)
        if dirty:
            errors.append(
                f"{packet_dir}/ has uncommitted changes -- commit the canonical packet "
                "proof bundle BEFORE signing, since the trusted acceptance engine reads "
                "it from committed git blobs, not the working tree: "
                + "; ".join(dirty[:5])
            )
    # Same class of bug as report_file/review_bundle_dir above: a TRACKED
    # symlink at packet_proof_path can be clean per git status (the symlink
    # itself is committed) while is_file()/read_text() follow it to valid
    # JSON elsewhere on disk -- but CI reads the committed blob bytes, which
    # for a symlink is the target PATH STRING, not JSON, and rejects it as
    # malformed. Must reject the symlink here too, independent of dirty-check.
    if packet_dir_ok and packet_proof_path.is_symlink():
        errors.append(f"{packet_proof_path} is a symlink, not a real file")
    elif packet_dir_ok and not packet_proof_path.is_file():
        errors.append(f"{packet_proof_path} not present")
    elif packet_dir_ok:
        try:
            packet_proof = json.loads(packet_proof_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{packet_proof_path} is malformed JSON: {exc}")
            packet_proof = {}
        if packet_proof.get("packet_id") != packet_id:
            errors.append(
                f"{packet_proof_path} packet_id={packet_proof.get('packet_id')!r} "
                f"!= derived PACKET_ID {packet_id!r}"
            )
        if packet_proof.get("head_sha") != proof.get("head_sha"):
            errors.append(
                f"{packet_proof_path} head_sha={packet_proof.get('head_sha')!r} "
                f"!= PR proof head_sha {proof.get('head_sha')!r}"
            )
        packet_embedded = packet_proof.get("embedded_audit") or {}
        for field in ("status", "auditor_tool", "auditor_model"):
            if packet_embedded.get(field) != embedded.get(field):
                errors.append(
                    f"{packet_proof_path} embedded_audit.{field}="
                    f"{packet_embedded.get(field)!r} != PR proof's {embedded.get(field)!r}"
                )
        if schema is not None:
            errors.extend(
                f"{packet_proof_path} embedded_audit.{e}"
                for e in schema_validation_errors(packet_embedded, schema)
            )
            errors.extend(
                f"{packet_proof_path} embedded_audit.{e}"
                for e in policy_errors(packet_embedded)
            )

if errors:
    print("proof will be REJECTED by CI:", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    sys.exit(1)
print(f"proof shape OK (audited head {proof['head_sha']})")
PY

ssh-keygen -Y sign -f "$KEY_PATH" -n "$NAMESPACE" "$PROOF_FILE"
echo "signed: ${PROOF_FILE}.sig"
echo
echo "Next steps:"
echo "  git add ${PROOF_DIR}/"
echo "  git commit -m 'proof(audit): signed local embedded-audit attestation for PR ${PR_NUMBER}'"
echo "  git push"
echo "(that commit must be the only change on top of the audited head_sha)"
