---
id: TP-DMX-DDF-DOCS-001
title: Development Factory Documentation — Foundation Docs
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-06'
status: DONE
prelude: Materializes the Dopemux Development Factory v1 design conversation into repo-native governance documentation (architecture, autonomy model, model routing, obligation ledger, execution capsule, build series, red lines, verification gates).
---
# Task Packet: TP-DMX-DDF-DOCS-001 · Development Factory · Foundation Docs

════════════════════════════════════════════════════════════

## Objective

Materialize the Dopemux Development Factory v1 design conversation into repo-native governance docs — extracted decisions, architecture, workflow, and gates only, not transcript dumps.

────────────────────────────────────────────────────────────

## Scope

IN:

* `docs/03-reference/development-factory/` — 15 documentation files
* `task-packets/development-factory/TP-DMX-DDF-DOCS-001.md` — this packet
* `proof/TP-DMX-DDF-DOCS-001/` — PROOF.json + SUMMARY.md

OUT:

* Schemas (`schemas/development-factory/*`) — deferred to later packets
* Config (`config/ai/*`) — deferred to `TP-DMX-MODEL-ROUTING-POLICY-001`
* Execution templates (`task-packets/templates/*`) — deferred to `TP-DMX-EXECUTION-CAPSULE-SCHEMA-001`
* Any executable code, tests, or CI changes

────────────────────────────────────────────────────────────

## Invariants (Must Remain True)

* No files created outside the three in-scope directories.
* No schemas, config, or templates created (deferred per build series).
* All component statuses reflect static analysis only (`runtime_process_verified: false`).
* `claudedocs/` and session memory are advisory only — never primary evidence.
* PROOF.json `head_sha` matches the actual `git rev-parse HEAD` at execution time.

If an invariant appears impossible, stop and report.

────────────────────────────────────────────────────────────

## Plan (Numbered)

1. Read the authoritative plan and the three source artifacts (`full-chat.md`, `Pasted markdown.md`, `dopemux-inv.md`).
2. Create `docs/03-reference/development-factory/` with 15 docs (README, architecture, process, autonomy-ladder, model-routing, obligation-ledger, execution-capsule, project-workstream-registry, evidence-and-proof-flow, pr-steward-and-readiness, learning-loop, red-lines-and-stop-conditions, build-series, open-questions, decision-record).
3. Create this task packet.
4. Generate the proof bundle (PROOF.json + SUMMARY.md) with the real HEAD SHA.
5. Run verification: 15 docs, packet present, proof present, scope confined, no schemas/config.

Keep steps mechanical and verifiable.

────────────────────────────────────────────────────────────

## Files to Touch

* `docs/03-reference/development-factory/README.md`
* `docs/03-reference/development-factory/architecture.md`
* `docs/03-reference/development-factory/process.md`
* `docs/03-reference/development-factory/autonomy-ladder.md`
* `docs/03-reference/development-factory/model-routing.md`
* `docs/03-reference/development-factory/obligation-ledger.md`
* `docs/03-reference/development-factory/execution-capsule.md`
* `docs/03-reference/development-factory/project-workstream-registry.md`
* `docs/03-reference/development-factory/evidence-and-proof-flow.md`
* `docs/03-reference/development-factory/pr-steward-and-readiness.md`
* `docs/03-reference/development-factory/learning-loop.md`
* `docs/03-reference/development-factory/red-lines-and-stop-conditions.md`
* `docs/03-reference/development-factory/build-series.md`
* `docs/03-reference/development-factory/open-questions.md`
* `docs/03-reference/development-factory/decision-record.md`
* `task-packets/development-factory/TP-DMX-DDF-DOCS-001.md`
* `proof/TP-DMX-DDF-DOCS-001/PROOF.json`
* `proof/TP-DMX-DDF-DOCS-001/SUMMARY.md`

If additional files are needed, stop and request approval.

────────────────────────────────────────────────────────────

## Exact Commands to Run

* ls docs/03-reference/development-factory/ | wc -l
* ls task-packets/development-factory/
* ls proof/TP-DMX-DDF-DOCS-001/
* git status --porcelain
* ls schemas/development-factory/ 2>/dev/null
* ls config/ai/ 2>/dev/null

────────────────────────────────────────────────────────────

## Output Capture Rules (Verbatim)

Implementer must return:

* git status --porcelain (untracked-aware; `git diff --name-only` does NOT list new files)
* Command outputs verbatim
* Exit codes
* The 18-file scope confirmation

────────────────────────────────────────────────────────────

## Embedded Audit

Docs-only packet — no executable code, schema, prompt, proof contract, security, or authority-boundary surface is changed. The docs themselves are advisory governance content drawn verbatim from the approved plan.

* auditor tool and model: NOT_RUN (no code surface to review)
* skip reason: docs-only; content is a direct transcription of the approved plan spec
* PAL codereview: NOT_RUN — no executable change

────────────────────────────────────────────────────────────

## PR Steward Readiness

No PR opened by this packet. Create + verify is the whole deliverable. If a PR is later opened, PR Steward must be the check-only review-intake gate per `docs/03-reference/development-factory/pr-steward-and-readiness.md`.

────────────────────────────────────────────────────────────

## Proof Bundle Expectations

Proof bundle at `proof/TP-DMX-DDF-DOCS-001/`:

* `PROOF.json` — repo identity, branch, head_sha, worktree_path, files_changed, validations (PASS/FAIL/NOT_RUN), pal_codereview_status, precommit_status, residual_risks, unknowns, stop_conditions_met, cleanup_status
* `SUMMARY.md` — human-readable summary, what was/was not created, evidence caveat, next step

────────────────────────────────────────────────────────────

## Acceptance Criteria

* `ls docs/03-reference/development-factory/ | wc -l` returns 15.
* `ls task-packets/development-factory/` shows `TP-DMX-DDF-DOCS-001.md`.
* `ls proof/TP-DMX-DDF-DOCS-001/` shows `PROOF.json` and `SUMMARY.md`.
* `git status --porcelain` confined to the three in-scope directories.
* `schemas/development-factory/` and `config/ai/` do not exist.

Each criterion is testable.

────────────────────────────────────────────────────────────

## Follow-Up

* Next packet: `TP-DMX-EVIDENCE-GATE-VERIFY-001` (re-verify key INFERRED component statuses from runtime).
* Full ordered series in `docs/03-reference/development-factory/build-series.md`.

## Source Context

Per `full-chat.md §4`, the five chat artifacts that produced this packet series:

1. Development Factory File Assembly Recon
2. Dopemux Development Factory v1 — Architecture + Build Plan
3. Stage-based model routing note
4. Patched DCP Component Census + Forgotten Work Evidence Pack (`Pasted markdown.md`)
5. Audit of DCP Component Census + Forgotten Work Recon (`dopemux-inv.md`)

────────────────────────────────────────────────────────────

## Rollback Steps

* Untracked: `rm -rf docs/03-reference/development-factory/ task-packets/development-factory/ proof/TP-DMX-DDF-DOCS-001/`
* If committed: `git reset --soft HEAD~1` then remove the directories above.

Keep rollback explicit.

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stop immediately if:

* A write would land outside the three in-scope directories.
* A schema, config, or template file is about to be created.
* The HEAD SHA cannot be resolved for the proof bundle.

If stopped, return what was attempted, evidence collected, and what output is needed next.
