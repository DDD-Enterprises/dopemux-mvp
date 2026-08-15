# Signing disclosure — PR #1224 local attestation (R7)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-PR-PREP-SPECIALIST-V2-001` / PR #1224, round R7.

## Prior rounds, briefly (full detail on record, unaltered)

- **R4**: independently audited PASS, 9 canonical + 10 compat files
  repaired against a 19-path frozen ACTIVE_CONTRADICTION census.
- **R5**: merged `main` for branch-protection up-to-date closure. Initial
  whole-tree audit FAIL on real-but-out-of-scope, pre-existing conflict
  markers (preserved as historical evidence, operator-adjudicated out of
  scope); scoped re-audit PASS. Reached `READY_FOR_OPERATOR_MERGE_DECISION`.
- **R6**: operator revoked R5 readiness after fresh evidence outranked it
  — main had advanced 9 more commits, 4 live review threads reported
  broken compatibility links, and the R3/R4 census was a genuine false
  negative (never searched for `TP-PRPS-000`/`7-step`, missing 6 adapter
  families still declaring a retired V1 contract). R6 merged main, ran an
  expanded census, repaired 12 files + 6 broken links, added regression
  tests. Independently re-audited PASS with explicit instruction not to
  trust the claimed file list. Reached `READY_FOR_OPERATOR_MERGE_DECISION`
  again, at head `f4fa9c2555cec4e1f40fc736c71609e55ecdb804`.

## Why R7 exists, and what it deliberately is not

After R6 reached readiness, `main` advanced 16 further commits (base
`f0a0e839b456eab05aa6b3592fdebb31c488fa5b` → tip
`75b4cfc581786a53445e412bfc8e25a6e0fdb978`), entirely Second Brain ADR
contract/evidence work. Before merging, drift was classified: 58 files
touched by main, **zero** path overlap with the 105 files this branch had
changed since the R6 base (verified via `comm -12`), and no touch to the
embedded-audit trust machinery (`schemas/proof/embedded_audit.schema.json`,
`scripts/audit/local_audit_acceptance.py`).

The operator explicitly scoped this as a **narrow drift closure**, not a
new semantic repair round and not a re-audit of R1-R6 substance: merge
`main` with a normal merge commit, verify nothing PR-Prep-owned changed,
re-verify the deterministic gates, and stop.

## R7 closure

1. Merged current `origin/main` (operator-authorized normal merge commit,
   not rebase/squash/force-push). `C1-R7 = 488e6b89773255ac08b915a2bc6ba6e489a33ce2`,
   two parents: `f4fa9c2555cec4e1f40fc736c71609e55ecdb804` (R6 head),
   `75b4cfc581786a53445e412bfc8e25a6e0fdb978` (main tip). Clean merge, no
   conflicts.
2. Verified `git diff --exit-code` over R6's full owned-surface set
   (`docs/03-reference/pr-pipeline/prep`, `docs/pr_prep`, `docs/pr_merge`,
   `tests/governance/test_pr_prep_contract_v2.py`,
   `task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.{json,md}`,
   `proof/TP-DMX-PR-PREP-SPECIALIST-V2-001`,
   `proof/pr_merge/embedded-audit/pr-1224`) between R6 head and C1-R7 —
   exit 0, empty diff. Zero conflict markers in that same universe.
3. Re-ran the R6 census patterns, the whole-`docs/pr_prep/**`
   link-resolution scan, the full governance suite (220 passed, PR-Prep
   count unchanged), schema validation, and the `origin/main` drift check
   (0 behind) — all clean.
4. One fresh independent L2 audit against exact `C1-R7`, explicitly
   scoped narrower than R6 (confirm the merge is inert with respect to
   this packet, not re-derive R1-R6 substance): **PASS** on all 10 scope
   items.

Full findings verbatim in
`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AUDITOR_REPAIR_3_REPORT.md` (raw
transcript: `AGY_AUDIT_RAW_R7.txt`). This `PROOF.json` and signature
replace the prior R6 proof at this same path; R1-R6 evidence remain on
record unaltered at `proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/`.

## What this bridge is, and is not

This is **not** a new repair, nor a re-audit of the substantive code
beyond the R7 audit already on record. It is a proof-only publication
step that lets the trusted embedded-audit CI gate accept that evidence.
Three heads are in play, named rather than conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (R7) | merge commit, examined by the R7 audit | `488e6b89773255ac08b915a2bc6ba6e489a33ce2` |
| `AUDIT_EVIDENCE_HEAD` (R7) | proof-only successor adding the R7 audit report/prompt/raw-transcript | `3fa5c8e97b998734205a2dbd42a282ff82625ce6` |
| `SIGNED_PROOF_HEAD` (this bridge) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1224/**` | the PR #1224 head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD` (R7). Its delta from
`AUDITED_TREE` (R7) is proof-only
(`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/{AUDITOR_REPAIR_3_REPORT.md,AGY_AUDIT_RAW_R7.txt,S4_AUDIT_PROMPT_R7.md}`
exclusively); no substantive byte changed after `AUDITED_TREE`. Verify
with:

```
git diff --exit-code 488e6b89773255ac08b915a2bc6ba6e489a33ce2..3fa5c8e97b998734205a2dbd42a282ff82625ce6 -- \
  docs/03-reference/pr-pipeline/prep docs/pr_prep docs/pr_merge tests/governance task-packets
```

This bridge commit's own diff on top of `AUDIT_EVIDENCE_HEAD` is confined
strictly to `proof/pr_merge/embedded-audit/pr-1224/**` — the
local-attestation acceptance script
(`scripts/audit/local_audit_acceptance.py`) enforces that the delta from
the audited `head_sha` to the enforced PR head touches **only** that
directory, so the audit-evidence files had to land in a separate, earlier
commit rather than alongside `PROOF.json`.

## The audit already on record

| Round | Runner | Model | Independence | Verdict |
|---|---|---|---|---|
| R4 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer | `PASS` |
| R5-initial | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer | `FAIL` (whole-tree conflict-marker scope item; out-of-scope; preserved as historical evidence) |
| R5-scoped | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer | `PASS` (subsequently revoked by operator decision, superseded by R6) |
| R6 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; instructed not to trust the claimed file list | `PASS` (0 findings, independently re-derived) |
| R7 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; scoped narrower than R6 by explicit operator instruction | `PASS` (0 findings, confirms the drift-closure merge is inert) |

This packet's controlling verdict is the R7 audit (PASS). This bridge does
not weaken or replace that governance; it exists solely to satisfy CI's
mechanical requirement for a schema-conformant, signed `embedded_audit`
object bound to PR #1224 so the `embedded-audit` and `PR Steward`
workflows can execute.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165/#1223/#1225 precedent). The R6 override for this same path already
expired after producing one signature. The operator granted a **fresh**
override for this R7 bridge commit, via an `AskUserQuestion` confirmation
in-session (recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1224 only
- authorized audit lineage: `AUDITED_TREE 488e6b89773255ac08b915a2bc6ba6e489a33ce2`,
  `AUDIT_EVIDENCE_HEAD 3fa5c8e97b998734205a2dbd42a282ff82625ce6`
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
#1165/#1223/#1225 precedent — `scripts/audit/sign_local_audit_proof.sh` can
print `signed: <path>.sig` when no new signature was actually created, if a
stale `.sig` already exists and `ssh-keygen` declines an overwrite prompt on
EOF), the procedure did not trust wrapper stdout alone:

1. the prior R6 `PROOF.json.sig` (signed over the R6 `head_sha`) was removed
   before re-signing;
2. the signer was invoked over the R7 `PROOF.json`, already schema-validated
   (`python3 scripts/audit/validate_audit_proof.py` — PASS);
3. the result was **independently verified** with
   `ssh-keygen -Y verify -f config/audit/embedded-audit-allowed-signers
   -I hue@local -n dopemux-embedded-audit -s PROOF.json.sig < PROOF.json` →
   `Good "dopemux-embedded-audit" signature for hue@local with ED25519 key
   SHA256:a+KnwksjkJWTgVwHtYzcSY5F14Isvcvb/doMYYVEQN8`;
4. `.sig` mtime confirmed to postdate `PROOF.json` mtime, confirming a fresh
   signature rather than a stale reused one.

## What this bridge explicitly does not authorize

**No merge** — the operator's authorization stops at a fresh
`READY_FOR_OPERATOR_MERGE_DECISION`; a separate, explicit merge
authorization is required, same as the PR #1225 precedent. No force push.
No history rewrite. No branch deletion. No production mutation. No
further re-audit beyond the R7 PASS. No substantive change — this
commit's diff versus `AUDIT_EVIDENCE_HEAD` is confined to
`proof/pr_merge/embedded-audit/pr-1224/**`.

PR #1224 was already marked ready for review at R5 and has remained
non-draft since; no mark-ready action is expected at this round. The
implementer will check CI + Steward at the exact final head and stop at a
fresh `READY_FOR_OPERATOR_MERGE_DECISION`.
