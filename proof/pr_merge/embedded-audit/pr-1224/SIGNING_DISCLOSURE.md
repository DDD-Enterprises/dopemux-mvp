# Signing disclosure — PR #1224 local attestation (canonical embedded-audit bridge)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-PR-PREP-SPECIALIST-V2-001` / PR #1224.

## What this bridge is, and is not

This is **not** a new repair, a new audit, or a re-audit of the substantive
code. It is a proof-only publication step that lets the trusted
embedded-audit CI gate accept evidence this packet already produced. Three
heads are in play, named rather than conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (C1-R4) | frozen substantive content, examined by the S4 audit | `6f32ac97dfd64f4386182fdd24380b2817551303` |
| `AUDIT_EVIDENCE_HEAD` | proof-only successor adding the audit report/route evidence | `efdaf2d42bb679fcea0e7c1d0bdf2b8011c4595a` |
| `SIGNED_PROOF_HEAD` (this bridge) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1224/**` | the PR #1224 head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD`. Its delta from `AUDITED_TREE`
is proof-only (`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/CONTENT_HEAD_R4.txt`,
`MODEL_ROUTE.json`, `AUDITOR_REPORT.md` exclusively); no substantive byte
changed after C1-R4. Verify with:

```
git diff --exit-code 6f32ac97dfd64f4386182fdd24380b2817551303..efdaf2d42bb679fcea0e7c1d0bdf2b8011c4595a -- \
  docs/03-reference/pr-pipeline/prep docs/pr_prep docs/pr_merge tests/governance task-packets
```

## The audit already on record

One S4 independent audit was produced for this packet before this bridge
existed:

| Runner | Model | Independence | Verdict |
|---|---|---|---|
| AGY / Google Antigravity CLI | `gemini-3.1-pro-high` (exact-model-verified via live `agy models` catalog, not inferred from branding) | separate CLI process and model family from the implementer (Claude Sonnet, this session); instructed not to trust implementer framing and to verify independently | `PASS` (0 risks flagged, 12/12 required scope items) |

Full 12-point findings are carried verbatim in
`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AUDITOR_REPORT.md`. This bridge does
not weaken or replace that governance; it exists solely to satisfy CI's
mechanical requirement for a schema-conformant, signed `embedded_audit`
object bound to PR #1224 so the `embedded-audit` and `PR Steward` workflows
can execute.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165/#1223 precedent). The operator granted a fresh override for this
bridge commit only, via an `AskUserQuestion` confirmation in-session
(recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1224 only
- authorized audit lineage: `AUDITED_TREE 6f32ac97dfd64f4386182fdd24380b2817551303`,
  `AUDIT_EVIDENCE_HEAD efdaf2d42bb679fcea0e7c1d0bdf2b8011c4595a`
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
#1165/#1223 precedent — `scripts/audit/sign_local_audit_proof.sh` can print
`signed: <path>.sig` when no new signature was actually created, if a stale
`.sig` already exists and `ssh-keygen` declines an overwrite prompt on EOF),
the procedure did not trust wrapper stdout alone:

1. any pre-existing `PROOF.json.sig` at this path was removed before signing
   (none existed — first signature for this path);
2. the signer was invoked over this exact, already schema-validated
   `PROOF.json` (`python3 scripts/audit/validate_audit_proof.py` — PASS);
3. the result was **independently verified** with
   `ssh-keygen -Y verify -f config/audit/embedded-audit-allowed-signers
   -I hue@local -n dopemux-embedded-audit -s PROOF.json.sig < PROOF.json` →
   `Good "dopemux-embedded-audit" signature for hue@local with ED25519 key
   SHA256:a+KnwksjkJWTgVwHtYzcSY5F14Isvcvb/doMYYVEQN8`;
4. `.sig` mtime (20:35) confirmed to postdate `PROOF.json` mtime (20:28),
   confirming a fresh signature rather than a stale reused one.

## What this bridge explicitly does not authorize

No mark-ready. No merge. No force push. No history rewrite. No branch
deletion. No production mutation. No re-audit of C1-R4. No substantive
change — this commit's diff versus the `AUDIT_EVIDENCE_HEAD` is confined to
`proof/pr_merge/embedded-audit/pr-1224/**`.
