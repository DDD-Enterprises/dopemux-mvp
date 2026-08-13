# Signing disclosure — PR #1224 local attestation (R6)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-PR-PREP-SPECIALIST-V2-001` / PR #1224, round R6.

## Why R6 supersedes the R5 proof at this same path

R5 (`AUDITED_TREE a89c11dbfd9d132797575118f3f7b8c4f819a2ab`, controlling
verdict PASS via a scoped re-audit) reached `READY_FOR_OPERATOR_MERGE_DECISION`,
but the operator **revoked** that readiness after fresh repository truth
outranked the prior claims:

1. `main` had advanced 9 commits past the R5 head (an independently
   audited change to the embedded-audit schema/acceptance tests among
   them), staling the R5 exact-head readiness.
2. **Four live unresolved review threads** (`copilot-pull-request-reviewer`)
   reported broken compatibility relative links under
   `docs/pr_prep/adapters/{vibe,codex}/**`. Confirmed real by direct read.
3. **A false-negative census.** The R3/R4 terminal semantic census scanned
   for fixed-artifact/risk-hint/GO_* vocabulary but never for
   `TP-PRPS-000` or `7-step`. Six adapter README families (claude, cursor,
   gemini, jules, copilot, vibe — codex was already correctly repaired at
   R4) still actively declared `Contract: TP-PRPS-000-1.0.0`, a "7-step
   canonical workflow", and `Status: IMPLEMENTED AND COMPLIANT`, in both
   canonical and compatibility form. Confirmed real by direct read of
   every matched file, not by trusting the grep hit count.

## R6 closure

1. Merged current `origin/main` into the branch (operator-authorized
   normal merge commit, not rebase/squash/force-push). Drift
   pre-classified `COMPATIBLE`: zero file-path overlap between the
   branch's 88 changed files (since merge-base `6626aa9a58`) and main's 23
   changed files over the same range, verified before merging.
   Pre-repair merge head: `4faa2d40a47b95713f5353f7e0d0f8e64b9e57af`.
2. Ran an expanded census (`TP-PRPS-000`, `7-step`, `seven-step`,
   `IMPLEMENTED AND COMPLIANT`, plus all prior R4 patterns) across
   `docs/03-reference/pr-pipeline/prep/**` and `docs/pr_prep/**`
   (non-archive). 32 pattern hits, every one read in full and classified:
   20 already correctly `RETIRED_PROSE` (left unedited), 12 genuine
   `ACTIVE_CONTRADICTION` (frozen in `R6_ACTIVE_CONTRADICTION_PATHS.txt`
   before any edit).
3. Repaired the 12 `ACTIVE_CONTRADICTION` files (canonical
   deprecation/pointer stubs + compat pointer stubs, matching the
   established R4 `codex` pattern) and separately fixed a 6-file
   broken-relative-link defect the R4 compat-stub template introduced
   (`../../03-reference` → `../../../03-reference`), including the 4
   files behind the live review threads plus 2 more found by grepping the
   whole compat tree for the same broken pattern.
4. Added regression tests: no live V1 contract markers in any R6-repaired
   file, every R6 compat stub declares compatibility-surface-only, and
   every relative link in every non-archive `docs/pr_prep/**` markdown
   file resolves on disk. 92 → 157 governance tests, all passing.
5. Frozen as `C1-R6 = ecab6aba71e204fc47337bee13b37e1b715dc37d`.
6. One fresh independent L2 audit against exact `C1-R6`, explicitly
   instructed not to trust the claimed file list and to independently
   re-derive the adapter-family census and link-resolution scan: **PASS**
   on all 9 scope items — 0 commits behind main, all 7 adapter platforms
   independently re-scanned and confirmed clean, a custom whole-tree
   link-resolution script found 0 broken links, the 4 originally-flagged
   links confirmed resolving, retired-prose files confirmed untouched,
   157/157 tests, schema-valid with allowlist verified by direct read,
   pre-commit clean.

Full findings verbatim in
`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AUDITOR_REPAIR_2_REPORT.md` (raw
transcript: `AGY_AUDIT_RAW_R6.txt`). This `PROOF.json` and signature
replace the prior R5 proof at this same path; R1-R5 evidence remain on
record unaltered at `proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/`, including
the R5-initial whole-tree FAIL and the R5-scoped PASS.

## What this bridge is, and is not

This is **not** a new repair beyond what's already committed, nor a
re-audit of the substantive code beyond the R6 audit already on record. It
is a proof-only publication step that lets the trusted embedded-audit CI
gate accept that evidence. Three heads are in play, named rather than
conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (R6) | merge + repair commit, examined by the R6 audit | `ecab6aba71e204fc47337bee13b37e1b715dc37d` |
| `AUDIT_EVIDENCE_HEAD` (R6) | proof-only successor adding the R6 audit report/prompt/raw-transcript | `514b8d8c38daf564e9bd95ce9a9f8519ce9b4b95` |
| `SIGNED_PROOF_HEAD` (this bridge) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1224/**` | the PR #1224 head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD` (R6). Its delta from
`AUDITED_TREE` (R6) is proof-only
(`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/{AUDITOR_REPAIR_2_REPORT.md,AGY_AUDIT_RAW_R6.txt,S4_AUDIT_PROMPT_R6.md}`
exclusively); no substantive byte changed after `AUDITED_TREE`. Verify
with:

```
git diff --exit-code ecab6aba71e204fc47337bee13b37e1b715dc37d..514b8d8c38daf564e9bd95ce9a9f8519ce9b4b95 -- \
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
| R4 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer | `PASS` (0 risks flagged, 12/12 required scope items) |
| R5-initial | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer | `FAIL` (whole-tree conflict-marker scope item; real but pre-existing, out-of-scope; preserved as historical evidence) |
| R5-scoped | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; instructed explicitly not to re-litigate the out-of-scope whole-tree finding | `PASS` (0 blocking findings within the packet-owned audit universe) — **subsequently revoked by operator decision, superseded by R6, not by staleness alone** |
| R6 | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; instructed explicitly not to trust the claimed file list and to independently re-derive the census and link scan | `PASS` (0 findings, all 9 scope items independently re-verified) |

This packet's controlling verdict is the R6 audit (PASS). This bridge does
not weaken or replace that governance; it exists solely to satisfy CI's
mechanical requirement for a schema-conformant, signed `embedded_audit`
object bound to PR #1224 so the `embedded-audit` and `PR Steward`
workflows can execute.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165/#1223/#1225 precedent). The R5 override for this same path already
expired after producing one signature. The operator granted a **fresh**
override for this R6 bridge commit, via an `AskUserQuestion` confirmation
in-session (recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1224 only
- authorized audit lineage: `AUDITED_TREE ecab6aba71e204fc47337bee13b37e1b715dc37d`,
  `AUDIT_EVIDENCE_HEAD 514b8d8c38daf564e9bd95ce9a9f8519ce9b4b95`
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

1. the prior R5 `PROOF.json.sig` (signed over the R5 `head_sha`) was removed
   before re-signing;
2. the signer was invoked over the R6 `PROOF.json`, already schema-validated
   (`python3 scripts/audit/validate_audit_proof.py` — PASS);
3. the result was **independently verified** with
   `ssh-keygen -Y verify -f config/audit/embedded-audit-allowed-signers
   -I hue@local -n dopemux-embedded-audit -s PROOF.json.sig < PROOF.json` →
   `Good "dopemux-embedded-audit" signature for hue@local with ED25519 key
   SHA256:a+KnwksjkJWTgVwHtYzcSY5F14Isvcvb/doMYYVEQN8`;
4. `.sig` mtime confirmed to postdate `PROOF.json` mtime, confirming a fresh
   signature rather than a stale reused one.

## What this bridge explicitly does not authorize

No mark-ready beyond the explicit condition below. **No merge** — the
operator's authorization stops at a fresh `READY_FOR_OPERATOR_MERGE_DECISION`;
a separate, explicit merge authorization is required, same as the PR
#1225 precedent. No force push. No history rewrite. No branch deletion.
No production mutation. No further re-audit beyond the R6 PASS. No
substantive change — this commit's diff versus `AUDIT_EVIDENCE_HEAD` is
confined to `proof/pr_merge/embedded-audit/pr-1224/**`.

**Mark-ready is conditionally authorized**: PR #1224 was already marked
ready for review during the R5 round and has not been reverted to draft;
if Steward nonetheless reports `PR_IS_DRAFT` as a blocker at this exact
head, the implementer may mark it ready again and re-run Steward. If
Steward reports any other blocker or unknown, halt and report back — do
not proceed further. **Review-thread resolution is authorized**: the 4
originally-flagged live threads may be classified, replied to, and
resolved once their underlying link defects are confirmed fixed at this
exact head. The implementer will check CI + Steward at the exact final
head and stop at a fresh `READY_FOR_OPERATOR_MERGE_DECISION`.
