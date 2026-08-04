---
id: TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
title: DCP Workflow Seam Lift (Narrow Carve-out)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-03'
last_review: '2026-08-03'
next_review: '2026-09-02'
prelude: L2 task packet for a narrow DCP-RED-MERGE-SEAM-0001 carve-out admitting
  two named workflow files for future editing.
---
# Task Packet: TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R

## Decision

```text
PACKET_STATUS=S3_REPAIR_IN_PROGRESS
S0_CUSTODY=ACCEPTED_FOR_PROGRESSION
S1_ADR_224=IMPLEMENTED
S2_GUARD_CARVEOUT_AND_TESTS=AUTHORIZED_AND_IMPLEMENTED
S3_PACKET_SCOPE_REPAIR_AND_BASELINE_PROOF=IN_PROGRESS
S4_PUSH_AND_DRAFT_PR=CONDITIONALLY_AUTHORIZED
S5_INDEPENDENT_AUDIT=NOT_YET_RUN
S6_WORKFLOW_CONTENT_WIRING=NOT_AUTHORIZED
RISK_LANE=L2
OBSERVED_MAIN_SHA=ff08e573b4259ac7456dae1a9985968603e9111d
IMPLEMENTATION_HEAD=9e113e68d0
IMPLEMENTATION_EVIDENCE=CLAIMED_LOCAL_NOT_REMOTE
MERGE_AUTHORITY=NOT_GRANTED
WORKFLOW_WIRING=NOT_AUTHORIZED
```

## Objective

Lift `DCP-RED-MERGE-SEAM-0001`'s blanket `.github/workflows/*` block just
enough to make two specific files —
`.github/workflows/embedded-audit.yml` and `.github/workflows/pr-steward.yml`
— editable via the normal Edit/Write tool path, without weakening the seam
for any other workflow file and without touching either file's content in
this packet. The concrete trigger was
`TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001` S3, which needed to wire a
new, already-tested function (`schema_validate_embedded_audit()`) into both
workflows and was hard-blocked by the seam's current blanket scope. See
`docs/90-adr/adr-224-dcp-workflow-seam-narrow-carveout.md` for full rationale,
alternatives considered, and consequences.

## Packet lineage note

A prior draft, `task-packets/TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001.json` (no `R`
suffix), already existed on `main`. It never validated against this repo's
canonical task-packet schema
(`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`) and mixes in
unrelated historical scope (a `workflow_run_identity.py` cherry-pick from a
different worktree branch, a `diagnostic_proof.py` extraction) that this
session never touched and was not asked to touch. This packet (`001R`)
supersedes it for the guard-carve-out scope; the old draft's unrelated `S3`/
`S4` steps are not carried forward. Full detail:
`proof/TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R/PACKET_SCOPE_REPAIR.md`.

## Authority and truth

- Operator authorization for Phase A (ADR + guard carve-out + tests) was
  granted, executed, and reviewed (`SEAM_LIFT_001R_PHASE_A=AUTHORIZED` →
  `SEAM_LIFT_001R_LOCAL_REVIEW=ACCEPT_WITH_DETERMINISTIC_PROOF_REPAIR`).
- Pushing the branch and opening a draft PR is **conditionally** authorized,
  gated on this repair commit's packet validating against the canonical
  schema and the baseline-failure proof classifying as `IDENTICAL`.
- Workflow content wiring (S6), marking the PR ready, and merge are **not**
  authorized by this packet.
- Runtime code, schemas, tests, and live GitHub state outrank this packet.

## Risk lane

**L2.** This packet changes a tool-enforced repo safety guard
(`DCP-RED-MERGE-SEAM-0001`'s `FORBIDDEN_PATHS`), which is more sensitive than
an ordinary code change but narrower in blast radius than the L3
auditor-admission work that triggered it (no proof/schema/CI-trust-boundary
change here — no workflow content is touched at all).

Required:

- narrow, exact-filename scope with negative tests proving the boundary;
- proof that `TEXT_RULES` content scanning is unaffected;
- deterministic proof that any test failure encountered is pre-existing, not
  a regression;
- one independent final audit (OpenCode/OpenRouter, distinct model family
  from the implementer) against the exact frozen pushed head before any
  further authorization is considered.

## Baseline-failure proof (required pre-push repair)

`tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`
fails on both unmodified `origin/main` (`ff08e573b4259ac7456dae1a9985968603e9111d`)
and this packet's implementation head (`9e113e68d0`), with byte-identical
output and exit code, in two independent clean detached worktrees. Root
cause: the test diffs against a fixed historical base ref
(`68f7435f6`, from an unrelated packet's markdown,
`task-packets/TP-DCP-0002.md`) that predates many since-merged, unrelated
workflow-touching PRs. Classification: `IDENTICAL` →
`BASELINE_EXISTING_STALE_ANCHOR`, non-blocking. Not repaired or suppressed
here, per instruction. Full detail:
`proof/TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R/BASELINE_FAILURE_PROOF.md`.

## Plan

- **S0** — custody: clean worktree off undrifted `origin/main`. Done.
- **S1** — ADR-224. Done.
- **S2** — guard carve-out + focused tests (hook layer + scanner layer,
  including a `TEXT_RULES`-still-active proof). Done, commit `9e113e68d0`.
- **S3** — this repair: packet lineage split from the disqualified `001`
  draft, schema-valid `001R` authored, baseline-failure proof produced. This
  stage's commit.
- **S4** — push branch, open draft PR (not ready-for-review). Conditionally
  authorized once S3 validates.
- **S5** — one independent final audit, OpenCode/OpenRouter, distinct model
  family from implementer, against the exact frozen pushed head. Not yet
  run.
- **S6** — wire the two workflow files' content. **Not authorized** by this
  packet; requires its own future authorization after this PR merges.

## Stop conditions

Stop and return to supervisor if:

- the baseline-failure proof is not `IDENTICAL` between `origin/main` and the
  candidate head;
- the draft PR's diff includes a fifth semantic file beyond the four
  implementation files plus packet/proof files;
- any other `.github/workflows/*` file becomes editable beyond the two named
  files;
- `TEXT_RULES` no longer blocks forbidden content inside either carved-out
  workflow file.
