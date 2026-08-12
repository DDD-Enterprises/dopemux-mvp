# Signing disclosure — PR #1225 local attestation (R4)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001` / PR #1225, round R4.

## Why R4 supersedes the R3 proof at this same path

R3 (`AUDITED_TREE 06abbf7119901bca1633728dd0ad12c9312857f6`) fixed two
Copilot review findings against R2 and was independently audited PASS.
While PR #1225 was in review, an automated Codex review flagged that
`task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json` failed
validation against the canonical Task Packet schema
(`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`): a
root-level `risk_lane` field is not a declared schema property (root
`additionalProperties: false`), and `execution.agent: "claude"` is not in
the schema's enum (`gemini`/`codex`/`vibe`/`shell`). A separate finding
flagged the packet's `commit.allowlist` did not cover
`proof/pr_merge/embedded-audit/pr-1225/**`. R4
(`fix(ci): make task packet schema-valid + record merge-proof in allowlist`,
commit `d1c261a80717ff37f7b62034e8e6a25e4c405d29`) fixes all three, with
**zero change to the matcher or test files** (independently confirmed by
the R4 auditor), and was independently re-audited. Any commit outside
`proof/pr_merge/embedded-audit/pr-1225/**` — including a metadata-only
task-packet-JSON fix — necessarily invalidates the prior proof's
ancestor/proof-only-delta binding by construction; this is expected
`local_audit_acceptance.py` behavior, not a defect. This `PROOF.json` and
signature replace the prior R3 proof at this same path; R1, R2, and R3
evidence remain on record at
`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/{AUDITOR_REPORT.md,AGY_AUDIT_RAW.txt,S4_AUDIT_PROMPT.md,AUDITOR_REPAIR_REPORT.md,AGY_AUDIT_RAW_R2.txt,S4_AUDIT_PROMPT_R2.md,AUDITOR_REPAIR_2_REPORT.md,AGY_AUDIT_RAW_R3.txt,S4_AUDIT_PROMPT_R3.md}`.

## What this bridge is, and is not

This is **not** a new repair beyond what's already committed, nor a
re-audit of the substantive code beyond the R4 audit already on record. It
is a proof-only publication step that lets the trusted embedded-audit CI
gate accept that evidence. Three heads are in play, named rather than
conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (R4) | frozen content, examined by the R4 S4 audit | `d1c261a80717ff37f7b62034e8e6a25e4c405d29` |
| `AUDIT_EVIDENCE_HEAD` (R4) | proof-only successor adding the R4 audit report/prompt/raw-transcript evidence | `b236c223e467d9c3301c3d297909e8fe5fb4401e` |
| `SIGNED_PROOF_HEAD` (this bridge) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1225/**` | the PR #1225 head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD` (R4). Its delta from
`AUDITED_TREE` (R4) is proof-only
(`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/{AUDITOR_REPAIR_3_REPORT.md,AGY_AUDIT_RAW_R4.txt,S4_AUDIT_PROMPT_R4.md}`
exclusively); no substantive byte changed after `AUDITED_TREE`. Verify with:

```
git diff --exit-code d1c261a80717ff37f7b62034e8e6a25e4c405d29..b236c223e467d9c3301c3d297909e8fe5fb4401e -- \
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
| R3 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; instructed to verify the "comment/test only" claim by diffing, not by trusting the commit message | `PASS` (0 findings, explicit confirmation the matcher's executable logic is byte-identical to R2) |
| R4 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; instructed to independently validate the prior commit against schema (confirming it DID fail) and the current head (confirming it does NOT) | `PASS` (0 findings, confirmed zero schema errors at current head vs. exactly the two claimed errors at the prior commit, matcher/tests confirmed unaffected) |

Full R4 findings are carried verbatim in
`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/AUDITOR_REPAIR_3_REPORT.md`
and the raw auditor transcript in `AGY_AUDIT_RAW_R4.txt` in the same
directory. This bridge does not weaken or replace that governance; it
exists solely to satisfy CI's mechanical requirement for a
schema-conformant, signed `embedded_audit` object bound to PR #1225 so the
`embedded-audit` and `PR Steward` workflows can execute.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165/#1223/#1224 precedent). The R3 override for this same path already
expired after producing one signature. The operator granted a **fresh**
override for this R4 bridge commit, via an `AskUserQuestion` confirmation
in-session (recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1225 only
- authorized audit lineage: `AUDITED_TREE d1c261a80717ff37f7b62034e8e6a25e4c405d29`,
  `AUDIT_EVIDENCE_HEAD b236c223e467d9c3301c3d297909e8fe5fb4401e`
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

1. the prior R3 `PROOF.json.sig` (signed over the R3 `head_sha`) was removed
   before re-signing;
2. the signer was invoked over the R4 `PROOF.json`, already schema-validated
   (`python3 scripts/audit/validate_audit_proof.py` — PASS);
3. the result was **independently verified** with
   `ssh-keygen -Y verify -f config/audit/embedded-audit-allowed-signers
   -I hue@local -n dopemux-embedded-audit -s PROOF.json.sig < PROOF.json` →
   `Good "dopemux-embedded-audit" signature for hue@local with ED25519 key
   SHA256:a+KnwksjkJWTgVwHtYzcSY5F14Isvcvb/doMYYVEQN8`;
4. `.sig` mtime confirmed to postdate `PROOF.json` mtime, confirming a fresh
   signature rather than a stale reused one (the gap between them reflects
   the operator's confirmation wait time for the scoped signing override,
   not tampering).

## What this bridge explicitly does not authorize

No mark-ready (already done separately, by explicit operator instruction).
No merge. No force push. No history rewrite. No branch deletion. No
production mutation. No further re-audit beyond R4. No substantive change —
this commit's diff versus `AUDIT_EVIDENCE_HEAD` is confined to
`proof/pr_merge/embedded-audit/pr-1225/**`. Per the L3 gate on this packet,
`merge=NOT_AUTHORIZED` remains in force regardless of this PASS verdict — a
separate, explicit merge authorization is required. This bridge also makes
no change to, and no claim about, PR #1224
(`TP-DMX-PR-PREP-SPECIALIST-V2-001`).
