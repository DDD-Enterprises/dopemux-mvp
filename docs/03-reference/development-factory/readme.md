---
id: readme
title: Readme
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Readme (reference) for dopemux documentation and developer workflows.
---
# Dopemux Development Factory

> ⚠️ **All evidence in this packet series is READY_WITH_RISKS.** Patched census reflects static analysis. No live process was verified. Compose-wiring ≠ runtime truth.

## What DDF Is

The Dopemux Development Factory (DDF) is a governed factory that turns architecture decisions into Execution Capsule packets, runs them under supervision, collects proof, and learns from results. It is a structured pipeline — not a mega-agent.

The factory's core loop:

1. Architecture decisions and research outputs enter as structured inputs.
2. The Execution Capsule Compiler converts them into scoped, authority-constrained packets.
3. A worktree/branch lease is acquired (one worktree per execution).
4. Implementation runs within the capsule's declared scope.
5. An embedded audit (PAL clink — external, not self-audit) verifies the work.
6. A proof bundle (`PROOF.json` + `SUMMARY.md`) is collected.
7. The PR Steward performs an advisory readiness check.
8. GPT-5.5 provides supervisor sign-off (go/no-go).
9. The obligation ledger is updated and a learning candidate is queued for human review.

Each stage proceeds only if the prior stage's gate passed. Any red-line trigger halts the capsule immediately.

## What DDF Is Not

- **Not autonomous execution.** Every consequential gate requires supervisor sign-off.
- **Not a live-write system.** `LIVE_WRITE_READY` is undefined. `DCP-RED-MERGE-SEAM-0001` is active. Live writes are blocked.
- **Not a mega-agent.** The factory is a pipeline of specialized components with declared authority slices.
- **Not a replacement for human review.** PR Steward is advisory only. Human review remains required before merge.

## Current Autonomy Status

| Level | Name | Status |
|-------|------|--------|
| L0 | Manual Planning | operational |
| L1 | Packet Factory | operational / READY_WITH_RISKS |
| L2 | Supervised Single Execution | cautious / supervised only |
| L3 | Supervised Batch | blocked |
| L4 | Auto Repair Loop | blocked |
| L5 | Auto PR + Review + Readiness | partial advisory only |
| L6 | Live Write / Execution Orchestration | blocked |

See [autonomy-ladder.md](autonomy-ladder.md) for full blocker detail.

## Next Packet

After this docs packet, the next is `TP-DMX-EVIDENCE-GATE-VERIFY-001`.

## Documents in This Directory

- [architecture.md](architecture.md) — Control plane hierarchy, component roles, authority slices, and the task-orchestrator naming contradiction.
- [process.md](process.md) — Full factory execution flow, stage gates, and halt conditions.
- [autonomy-ladder.md](autonomy-ladder.md) — L0–L6 autonomy ladder with current status and blockers for each level.
- [model-routing.md](model-routing.md) — Model routing policy: which model handles which factory stage and why.
- [obligation-ledger.md](obligation-ledger.md) — Append-only ledger of commitments, constraints, and deferred items.
- [execution-capsule.md](execution-capsule.md) — Execution Capsule schema: scope, authority constraints, proof requirements, halt conditions.
- [project-workstream-registry.md](project-workstream-registry.md) — Registry of active and queued project workstreams with status and ownership.
- [evidence-and-proof-flow.md](evidence-and-proof-flow.md) — How proof bundles are generated, validated, and linked to obligation ledger entries.
- [pr-steward-and-readiness.md](pr-steward-and-readiness.md) — PR Steward authority (advisory only), MERGE_READINESS artifacts, and what readiness means.
- [learning-loop.md](learning-loop.md) — How learning candidates are generated, reviewed, and accepted or rejected.
- [red-lines-and-stop-conditions.md](red-lines-and-stop-conditions.md) — Full red-line register: conditions that immediately halt capsule execution.
- [build-series.md](build-series.md) — Build series structure: how packets are grouped, ordered, and gated within a series.
- [open-questions.md](open-questions.md) — Unresolved authority questions, naming contradictions, and deferred design decisions.
- [decision-record.md](decision-record.md) — Durable record of DDF design decisions with rationale and alternatives considered.
