# Signing disclosure — PR #1235 local attestation

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
PR #1235.

## What this PR is

PR #1235 is a corrective revert. It undoes commit `e84d62caeebdc4dc4c1d793c97687a0d9722ebc7`
(TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001), which was itself an accidental,
unauthorized `main` write: an admin-permission `gh api -X PUT .../merge` call,
made while probing whether the newly-repaired branch-protection required
checks correctly block a normal merge, used a token that unconditionally
bypasses those checks (`enforce_admins=false`). That call merged a throwaway
canary probe file onto `main` without the two new required checks ever
reporting.

`git revert e84d62caeebdc4dc4c1d793c97687a0d9722ebc7 --no-edit` produces
commit `bbcd474a0fb81a160e68537eb56c5b195133072b`, restoring `main`'s tree to
exactly the state it had at the pre-incident tip
`75b4cfc581786a53445e412bfc8e25a6e0fdb978` — verified via an empty
`git diff 75b4cfc581786a53445e412bfc8e25a6e0fdb978 bbcd474a0f`.

## Why the trusted CI auditor can't run here

On `main=e84d62ca…` (containing the accidental commit), the trusted
embedded-audit workflow cannot locate its trusted audit emitter and no
signed `proof/pr_merge/embedded-audit/pr-1235/PROOF.json` existed at the PR
head, so it fails closed with `SKIPPED`/`NEEDS_SUPERVISOR`. This is the
gate working as designed — the same gate this incident exists to repair.

## Independent audit performed

`agy` CLI, `gemini-3.1-pro-high`, `--sandbox --mode plan` (read-only),
run against exact commit `bbcd474a0fb81a160e68537eb56c5b195133072b` via
SHA-addressed `git show`/`git diff`/`git log` (content-addressed
operations, valid independent of working-tree checkout state). Verdict
**PASS**: confirmed the commit touches exactly one file (deletion of
`CANARY_MERGE_GATE_PROBE.txt`), confirmed the tree is byte-identical to
the pre-incident `main` tip, confirmed the parent chain, confirmed no
schema/config/workflow paths are touched. Full report:
`proof/TP-DMX-CI-TRUST-MERGE-GATE-INCIDENT-001-REVERT-1235/AUDITOR_REPORT.md`
(raw transcript and prompt alongside it).

## Bridge topology, named not conflated

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` | commit examined by the independent audit | `bbcd474a0fb81a160e68537eb56c5b195133072b` |
| `AUDIT_EVIDENCE_HEAD` | proof-only successor adding only the audit report/transcript/prompt | `a4c9aef0150c7e900ab3f91e1bfe4c658d59bc3e` |
| this bridge commit | adds only `proof/pr_merge/embedded-audit/pr-1235/**` on top of `AUDIT_EVIDENCE_HEAD` | (this commit) |

`AUDITED_TREE` is an ancestor of `AUDIT_EVIDENCE_HEAD`; no substantive byte
changed after `AUDITED_TREE`. This bridge commit is itself a second
proof-only delta, not a re-audit.

## Trust model, stated plainly

This signature is a **producer/operator self-attestation**, not a
third-party audit. The independent evidence is the AGY run itself
(different model family, different runtime, run read-only against the
exact commit). The signature only lets the trusted CI workflow accept
that already-independent evidence when its own auditor cannot execute.

Authorized under a fresh, narrowly-scoped operator decision specific to
PR #1235 ("Authorize signed local attestation") — not inferred from any
earlier, broader authorization in this incident.

## Correction

The first signed PROOF.json committed for this PR (b601969da9) contained a
transcription error: `head_sha` was written as `a4c9aef0158e1f8bf13c7cfb8ce54c0b4dcb02f0`,
a similar-looking but incorrect SHA (diverges from the real
AUDIT_EVIDENCE_HEAD after the 9th hex digit). The trusted CI acceptance
check correctly rejected it (`objects_unreachable`), exactly as the
fail-closed design intends. This PROOF.json corrects `head_sha` to the
real AUDIT_EVIDENCE_HEAD, `a4c9aef0150c7e900ab3f91e1bfe4c658d59bc3e`, and
is re-signed accordingly.

## What this proof authorizes

Only readiness-check progression (exact-head CI + `PR Steward / final
readiness` going green) for PR #1235's actual code head,
`bbcd474a0fb81a160e68537eb56c5b195133072b`. Merge is performed separately,
pinned to that exact head via `expected_head_sha`, after confirming the
checks report green through the normal (non-bypass) path.
