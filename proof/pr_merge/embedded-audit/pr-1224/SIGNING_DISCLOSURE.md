# Signing disclosure — PR #1224 local attestation (R5)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-PR-PREP-SPECIALIST-V2-001` / PR #1224, round R5.

## Why R5 supersedes the R4 proof at this same path

R4 (`AUDITED_TREE 6f32ac97dfd64f4386182fdd24380b2817551303`, independently
audited PASS) was ready, but the branch was 19 commits behind `origin/main`
and GitHub branch protection requires the PR head to be up to date with
`main` before merge. The operator explicitly authorized a normal merge of
`origin/main` into the branch (`AUTHORIZE ... UP-TO-DATE CLOSURE` pattern,
consistent with the PR #1225 precedent) — not rebase, not squash, no
force-push — with drift pre-classified `COMPATIBLE` (zero file-path
overlap between the branch's 81 changed files since merge-base `3e8fcc1c70`
and main's 104 changed files over the same range, verified before
merging). R5 (`a89c11dbfd9d132797575118f3f7b8c4f819a2ab`, a genuine
two-parent merge commit) is the result.

Two independent audit rounds ran against this unchanged C1-R5:

1. **Round 1 (whole-tree scope): FAIL.** The whole-repository
   conflict-marker scan found real, pre-existing, unresolved markers in
   files with zero relationship to this packet. Deterministically proven
   byte-identical on both merge parents before the merge; traces to an
   unrelated 2026-03-30 commit. **Preserved unaltered as historical
   evidence** — not deleted, overwritten, or relabeled.
2. **Operator scope adjudication:** ruled the whole-tree finding out of
   scope for this packet — real debt, tracked separately, not this
   packet's blocker. Full reasoning:
   `proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AUDIT_R5_SCOPE_ADJUDICATION.md`.
3. **Round 2 (scoped to this packet's owned audit universe): PASS.**
   Re-verified the same, unchanged C1-R5, restricted to this packet's
   owned paths — zero packet-scoped conflict markers, zero content drift
   vs. the already-audited R4 state, 92/92 governance tests,
   schema-valid, docs-prohibited-patterns false positive (noted at R4)
   confirmed resolved, 0 commits behind main.

Full findings for both rounds are carried verbatim in
`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AUDITOR_REPAIR_REPORT.md`
(raw transcripts: `AGY_AUDIT_RAW_R5_INITIAL.txt`,
`AGY_AUDIT_RAW_R5_SCOPED.txt`). This `PROOF.json` and signature replace the
prior R4 proof at this same path; R1-R4 evidence remain on record at
`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/{AUDITOR_REPORT.md,BASELINE.json,COMMAND_LOG_R4.md,CONSUMER_INVENTORY.md,CONTENT_HEAD*.txt,CONTRACT_DECISIONS.md,DUPLICATE_PATH_MAP.json,LEGACY_SEMANTICS_SCAN_R3.md,LEGACY_SEMANTICS_SCAN_R4.md,MODEL_ROUTE.json,R2-SUPERVISOR-RULING.md,R3-SUPERVISOR-RULING.md,R4_ACTIVE_CONTRADICTION_PATHS.txt,R4_SCOPE_FREEZE.md,VALIDATION*.json}`.

## What this bridge is, and is not

This is **not** a new repair beyond what's already committed, nor a
re-audit of the substantive code beyond the two R5 audits already on
record. It is a proof-only publication step that lets the trusted
embedded-audit CI gate accept that evidence. Three heads are in play,
named rather than conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (R5) | merge commit, examined by both R5 audit rounds | `a89c11dbfd9d132797575118f3f7b8c4f819a2ab` |
| `AUDIT_EVIDENCE_HEAD` (R5) | proof-only successor adding the R5 audit reports/prompts/raw-transcripts/adjudication | `f33728b7848d5d1503117441a8750815065bb2ed` |
| `SIGNED_PROOF_HEAD` (this bridge) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1224/**` | the PR #1224 head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD` (R5). Its delta from
`AUDITED_TREE` (R5) is proof-only
(`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/{AUDITOR_REPAIR_REPORT.md,AGY_AUDIT_RAW_R5_INITIAL.txt,S4_AUDIT_PROMPT_R5_INITIAL.md,AGY_AUDIT_RAW_R5_SCOPED.txt,S4_AUDIT_PROMPT_R5_SCOPED.md,AUDIT_R5_SCOPE_ADJUDICATION.md,VALIDATION_R5.json}`
exclusively); no substantive byte changed after `AUDITED_TREE`. Verify
with:

```
git diff --exit-code a89c11dbfd9d132797575118f3f7b8c4f819a2ab..f33728b7848d5d1503117441a8750815065bb2ed -- \
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
| R5-scoped | AGY / Google Antigravity CLI | `gemini-3.1-pro-high` | separate CLI process and model family from the implementer; instructed explicitly not to re-litigate the out-of-scope whole-tree finding, and to restrict the conflict-marker check to this packet's own owned paths | `PASS` (0 blocking findings within the packet-owned audit universe; whole-tree debt explicitly labeled `PREEXISTING_REPO_DEBT` / non-blocking) |

This packet's controlling verdict is the R5-scoped audit (PASS), per
explicit operator scope adjudication. This bridge does not weaken or
replace that governance; it exists solely to satisfy CI's mechanical
requirement for a schema-conformant, signed `embedded_audit` object bound
to PR #1224 so the `embedded-audit` and `PR Steward` workflows can
execute.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165/#1223/#1225 precedent). The R4 override for this same path already
expired after producing one signature. The operator granted a **fresh**
override for this R5 bridge commit, via an `AskUserQuestion` confirmation
in-session (recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1224 only
- authorized audit lineage: `AUDITED_TREE a89c11dbfd9d132797575118f3f7b8c4f819a2ab`,
  `AUDIT_EVIDENCE_HEAD f33728b7848d5d1503117441a8750815065bb2ed`
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

1. the prior R4 `PROOF.json.sig` (signed over the R4 `head_sha`) was removed
   before re-signing;
2. the signer was invoked over the R5 `PROOF.json`, already schema-validated
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
operator's authorization stops at
`READY_FOR_OPERATOR_MERGE_DECISION`; a separate, explicit merge
authorization is required, same as the PR #1225 precedent. No force push.
No history rewrite. No branch deletion. No production mutation. No further
re-audit beyond the R5-scoped PASS. No substantive change — this commit's
diff versus `AUDIT_EVIDENCE_HEAD` is confined to
`proof/pr_merge/embedded-audit/pr-1224/**`.

**Mark-ready is conditionally authorized**: if and only if PR Steward
reports the sole blocker as `PR_IS_DRAFT` at this exact head (this bridge
commit's own SHA), the implementer may mark PR #1224 ready for review and
re-run Steward. If Steward reports any other blocker or unknown, halt and
report back — do not proceed further. The implementer will check CI +
Steward at the exact final head and stop at
`READY_FOR_OPERATOR_MERGE_DECISION`.
