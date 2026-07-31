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
python3 - "$PROOF_FILE" "$PR_NUMBER" <<'PY'
import json, re, sys
from pathlib import Path

proof_file, pr_number = Path(sys.argv[1]), int(sys.argv[2])
proof = json.loads(proof_file.read_text(encoding="utf-8"))
errors = []
if int(proof.get("pr_number") or 0) != pr_number:
    errors.append(f"pr_number={proof.get('pr_number')!r} != {pr_number}")
if not proof.get("repo"):
    errors.append("repo missing")
if not re.match(r"^[0-9a-f]{40}$", str(proof.get("head_sha") or "")):
    errors.append("head_sha missing or not a full 40-char sha")
embedded = proof.get("embedded_audit") or {}
if embedded.get("status") not in ("PASS", "PASS_WITH_RISKS"):
    errors.append(f"embedded_audit.status={embedded.get('status')!r} is not passing")
schema_path = Path("schemas/proof/embedded_audit.schema.json")
if schema_path.is_file():
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    for field in ("auditor_tool", "auditor_model"):
        enum = props.get(field, {}).get("enum", [])
        if embedded.get(field) not in enum:
            errors.append(
                f"embedded_audit.{field}={embedded.get(field)!r} not in schema enum {enum}"
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
