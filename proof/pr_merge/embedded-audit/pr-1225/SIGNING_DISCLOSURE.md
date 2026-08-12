# Signing disclosure — PR #1225 local attestation

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001` / PR #1225.

## What this bridge is, and is not

This is **not** a new repair, a new audit, or a re-audit of the substantive
code. It is a proof-only publication step that lets the trusted
embedded-audit CI gate accept evidence this packet already produced. Three
heads are in play, named rather than conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` | frozen substantive content, examined by the S4 audit | `fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a` |
| `AUDIT_EVIDENCE_HEAD` | proof-only successor adding the audit report/prompt/raw-transcript evidence | `67ec086d71b4b8df37244f513450067a04688e52` |
| `SIGNED_PROOF_HEAD` (this bridge) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1225/**` | the PR #1225 head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD`. Its delta from
`AUDITED_TREE` is proof-only
(`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/{AUDITOR_REPORT.md,AGY_AUDIT_RAW.txt,S4_AUDIT_PROMPT.md}`
exclusively); no substantive byte changed after `AUDITED_TREE`. Verify with:

```
git diff --exit-code fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a..67ec086d71b4b8df37244f513450067a04688e52 -- \
  .pre-commit-config.yaml scripts/ci/docs_prohibited_patterns.sh \
  tests/ci/test_docs_prohibited_patterns.py \
  task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json
```

This bridge commit's own diff on top of `AUDIT_EVIDENCE_HEAD` is confined
strictly to `proof/pr_merge/embedded-audit/pr-1225/**` — the local-attestation
acceptance script (`scripts/audit/local_audit_acceptance.py`) enforces that
the delta from the audited `head_sha` to the enforced PR head touches
**only** that directory, so the audit-evidence files had to land in a
separate, earlier commit rather than alongside `PROOF.json`.

## The audit already on record

One S4 independent audit was produced for this packet before this bridge
existed:

| Runner | Model | Independence | Verdict |
|---|---|---|---|
| AGY / Google Antigravity CLI | `gemini-3.1-pro-high` (exact-model-verified via live `agy models` catalog, not inferred from branding) | separate CLI process and model family from the implementer (Claude Sonnet, this session); instructed not to trust implementer framing and to verify independently, including by running commands itself | `PASS` (0 risks flagged, 10/10 required scope items) |

Full findings are carried verbatim in
`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/AUDITOR_REPORT.md` and the
raw auditor transcript in `AGY_AUDIT_RAW.txt` in the same directory. This
bridge does not weaken or replace that governance; it exists solely to
satisfy CI's mechanical requirement for a schema-conformant, signed
`embedded_audit` object bound to PR #1225 so the `embedded-audit` and
`PR Steward` workflows can execute.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165/#1223/#1224 precedent). The operator granted a fresh override for
this bridge commit only, via an `AskUserQuestion` confirmation in-session
(recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1225 only
- authorized audit lineage: `AUDITED_TREE fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a`,
  `AUDIT_EVIDENCE_HEAD 67ec086d71b4b8df37244f513450067a04688e52`
- expires immediately after one valid signature is produced; no standing
  signing authority granted

Accordingly:

- The signing script was invoked by the **producer** (Claude Code, this
  session), not by an independent party, using the operator's allow-listed
  key already provisioned on this machine.
- The signature covers this `PROOF.json` byte-for-byte.
- This override does **not** extend to any other packet, proof, or PR, and it
  does not weaken the signature-verification, allowed-signers,
  exact-head-binding, or proof-only-closure gates in
  `scripts/audit/local_audit_acceptance.py`, none of which were modified.

## How this signature was actually produced

Per the known signing-wrapper false-success defect (documented in the PR
#1165/#1223/#1224 precedent — `scripts/audit/sign_local_audit_proof.sh` can
print `signed: <path>.sig` when no new signature was actually created, if a
stale `.sig` already exists and `ssh-keygen` declines an overwrite prompt on
EOF), the procedure did not trust wrapper stdout alone. This proof was
re-signed once, after `head_sha` was corrected from a first attempt that
pointed at `AUDITED_TREE` directly (rejected by CI's local-attestation gate
because the audit-evidence files and `PROOF.json` had been committed
together, violating the proof-only-delta requirement — see the CI failure
log for run `31568477373`/job `94025186268`, `local audit attestation
REJECTED: delta_touches_code`). For this corrected signature:

1. the stale `PROOF.json.sig` (signed over the wrong `head_sha`) was removed
   before re-signing;
2. the signer was invoked over the corrected, already schema-validated
   `PROOF.json` (`python3 scripts/audit/validate_audit_proof.py` — PASS);
3. the result was **independently verified** with
   `ssh-keygen -Y verify -f config/audit/embedded-audit-allowed-signers
   -I hue@local -n dopemux-embedded-audit -s PROOF.json.sig < PROOF.json` →
   `Good "dopemux-embedded-audit" signature for hue@local with ED25519 key
   SHA256:a+KnwksjkJWTgVwHtYzcSY5F14Isvcvb/doMYYVEQN8`;
4. `.sig` mtime (23:04:52) confirmed to postdate `PROOF.json` mtime
   (23:04:43), confirming a fresh signature rather than a stale reused one.

## What this bridge explicitly does not authorize

No mark-ready. No merge. No force push. No history rewrite. No branch
deletion. No production mutation. No re-audit of `AUDITED_TREE`. No
substantive change — this commit's diff versus `AUDIT_EVIDENCE_HEAD` is
confined to `proof/pr_merge/embedded-audit/pr-1225/**`. Per the L3 gate on
this packet, `merge=NOT_AUTHORIZED` remains in force regardless of this PASS
verdict — a separate, explicit merge authorization is required. This bridge
also makes no change to, and no claim about, PR #1224
(`TP-DMX-PR-PREP-SPECIALIST-V2-001`).
