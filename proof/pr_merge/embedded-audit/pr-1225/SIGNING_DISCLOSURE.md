# Signing disclosure — PR #1225 local attestation (R2)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001` / PR #1225, round R2.

## Why R2 supersedes the R1 proof at this same path

R1 (`AUDITED_TREE fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a`) fixed the
original template/temp false-positive and was independently audited PASS.
While PR #1225 was in review, an automated Codex review
(`chatgpt-codex-connector`) flagged a real gap in R1: the blanket
`*template*) continue` short-circuited **all** prohibition checks, so
`todo-template.md` / `notes-template.md` / `temp-template.md` /
`scratch-template.md` were incorrectly allowed — a genuine policy-loosening
regression against the packet's own invariant. R2
(`fix(ci): keep notes/todo/scratch tokens blocked in template-named files`,
commit `833f8cdac448dbf93f7d70e44526674fa48b37c7`) fixes that gap and was
independently re-audited. This `PROOF.json` and signature replace the prior
R1 proof at this same path; R1's evidence remains on record at
`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/{AUDITOR_REPORT.md,AGY_AUDIT_RAW.txt,S4_AUDIT_PROMPT.md}`.

## What this bridge is, and is not

This is **not** a new repair beyond what's already committed, nor a
re-audit of the substantive code beyond the R2 audit already on record. It
is a proof-only publication step that lets the trusted embedded-audit CI
gate accept that evidence. Three heads are in play, named rather than
conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (R2) | frozen substantive content, examined by the R2 S4 audit | `833f8cdac448dbf93f7d70e44526674fa48b37c7` |
| `AUDIT_EVIDENCE_HEAD` (R2) | proof-only successor adding the R2 audit report/prompt/raw-transcript evidence | `b3274a54bacbe4ba8ca758ff5619782af77d329c` |
| `SIGNED_PROOF_HEAD` (this bridge) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1225/**` | the PR #1225 head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD` (R2). Its delta from
`AUDITED_TREE` (R2) is proof-only
(`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/{AUDITOR_REPAIR_REPORT.md,AGY_AUDIT_RAW_R2.txt,S4_AUDIT_PROMPT_R2.md}`
exclusively); no substantive byte changed after `AUDITED_TREE`. Verify with:

```
git diff --exit-code 833f8cdac448dbf93f7d70e44526674fa48b37c7..b3274a54bacbe4ba8ca758ff5619782af77d329c -- \
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

| Round | Runner | Model | Independence | Verdict |
|---|---|---|---|---|
| R1 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer | `PASS` (0 risks flagged, 10/10 required scope items) |
| R2 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; instructed not to trust implementer framing, verify independently, and actively probe adversarial edge cases | `PASS` (0 blocking risks flagged, 10/10 required scope items, incl. independent adversarial edge-case testing beyond the packet's own test suite) |

Full R2 findings are carried verbatim in
`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/AUDITOR_REPAIR_REPORT.md`
and the raw auditor transcript in `AGY_AUDIT_RAW_R2.txt` in the same
directory. This bridge does not weaken or replace that governance; it
exists solely to satisfy CI's mechanical requirement for a
schema-conformant, signed `embedded_audit` object bound to PR #1225 so the
`embedded-audit` and `PR Steward` workflows can execute.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165/#1223/#1224 precedent). The R1 override for this same path already
expired after producing one signature. The operator granted a **fresh**
override for this R2 bridge commit, via an `AskUserQuestion` confirmation
in-session (recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1225 only
- authorized audit lineage: `AUDITED_TREE 833f8cdac448dbf93f7d70e44526674fa48b37c7`,
  `AUDIT_EVIDENCE_HEAD b3274a54bacbe4ba8ca758ff5619782af77d329c`
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
EOF), the procedure did not trust wrapper stdout alone:

1. the prior R1 `PROOF.json.sig` (signed over the R1 `head_sha`) was removed
   before re-signing;
2. the signer was invoked over the R2 `PROOF.json`, already schema-validated
   (`python3 scripts/audit/validate_audit_proof.py` — PASS);
3. the result was **independently verified** with
   `ssh-keygen -Y verify -f config/audit/embedded-audit-allowed-signers
   -I hue@local -n dopemux-embedded-audit -s PROOF.json.sig < PROOF.json` →
   `Good "dopemux-embedded-audit" signature for hue@local with ED25519 key
   SHA256:a+KnwksjkJWTgVwHtYzcSY5F14Isvcvb/doMYYVEQN8`;
4. `.sig` mtime (23:29:29) confirmed to postdate `PROOF.json` mtime
   (23:29:21), confirming a fresh signature rather than a stale reused one.

## What this bridge explicitly does not authorize

No mark-ready (already done separately, by explicit operator instruction).
No merge. No force push. No history rewrite. No branch deletion. No
production mutation. No further re-audit beyond R2. No substantive change —
this commit's diff versus `AUDIT_EVIDENCE_HEAD` is confined to
`proof/pr_merge/embedded-audit/pr-1225/**`. Per the L3 gate on this packet,
`merge=NOT_AUTHORIZED` remains in force regardless of this PASS verdict — a
separate, explicit merge authorization is required. This bridge also makes
no change to, and no claim about, PR #1224
(`TP-DMX-PR-PREP-SPECIALIST-V2-001`).
