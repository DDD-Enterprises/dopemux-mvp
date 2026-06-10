---
id: process
title: Process
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Process (reference) for dopemux documentation and developer workflows.
---
# Development Factory — Execution Process

## Factory Execution Flow

```
research
  → architecture synthesis
  → build-series planning
  → execution capsule packet (scoped, authority-constrained)
  → worktree/branch lease (one worktree per execution)
  → implementation (within capsule scope)
  → embedded audit (PAL clink — not self-audit)
  → proof bundle (PROOF.json + SUMMARY.md)
  → PR (preflight gates must pass)
  → AI review / human review
  → PR Steward readiness check (advisory)
  → GPT-5.5 judgement (supervisor sign-off)
  → obligation ledger updates
  → learning candidate queue
```

## Stage Gates

Each stage may only proceed if the prior stage's gate passed. A red-line trigger at any stage halts the capsule immediately — see [red-lines-and-stop-conditions.md](red-lines-and-stop-conditions.md) for the full register.

### Research → Architecture Synthesis

**Gate**: Research output must be scoped to the target workstream. Conflicting findings must be explicitly surfaced and resolved before synthesis begins. Unresolved authority is marked `UNKNOWN`, not assumed.

### Architecture Synthesis → Build-Series Planning

**Gate**: The synthesized architecture must include a declared authority slice for every component it touches. Any component whose authority is `UNKNOWN` must be flagged in [open-questions.md](open-questions.md) before packets are generated.

### Build-Series Planning → Execution Capsule Packet

**Gate**: Each capsule must declare: scope boundaries, authority constraints, proof requirements, and halt conditions. Capsules that exceed declared scope at any point must halt and report — they may not self-expand.

### Execution Capsule Packet → Worktree/Branch Lease

**Gate**: One worktree per execution. The lease manager must confirm no existing lease is active for the same capsule before acquiring. Lease acquisition is atomic.

### Worktree/Branch Lease → Implementation

**Gate**: Implementation begins only inside the leased worktree. The capsule's declared scope is the hard boundary. Cross-cutting changes (CI files, shared config, `.taskorchestrator/config.yaml`) require explicit operator authorization per `AGENTS.md`.

### Implementation → Embedded Audit

**Gate**: Implementation must be committed before the audit runs. The embedded audit uses PAL clink (external model) — not the implementing agent auditing its own work. Self-audit does not satisfy this gate.

### Embedded Audit → Proof Bundle

**Gate**: The audit must produce a structured result (`PASS`, `PASS_WITH_RISKS`, or `FAIL`). A `FAIL` result halts the capsule. A `PASS_WITH_RISKS` result proceeds with all risks explicitly documented in `PROOF.json`. `NOT_RUN` is treated as `FAIL`.

### Proof Bundle → PR

**Gate**: All preflight gates in the CI configuration must pass before the PR is opened. The proof bundle (`PROOF.json` + `SUMMARY.md`) must be committed to the branch and referenced in the PR description.

### PR → AI Review / Human Review

**Gate**: At minimum, an AI review (PAL codereview, external model) must complete before the PR proceeds. Human review is required before merge. Reviews must be documented — passing without evidence does not satisfy this gate.

### AI Review / Human Review → PR Steward Readiness Check

**Gate**: The PR Steward intake (`tools/pr_steward/`) checks for `MERGE_READINESS` artifacts. **PR Steward is advisory only.** Its output informs the supervisor; it does not authorize merge. The PR Steward has read permissions only and must not invoke `queue_drain.py`.

### PR Steward Readiness Check → GPT-5.5 Judgement

**Gate**: The supervisor (GPT-5.5) receives the full evidence package: proof bundle, audit result, AI review, human review, PR Steward readiness artifact. The supervisor's judgement is the go/no-go decision. This is the single authoritative decision point in the pipeline. A `no-go` result closes the PR and returns the capsule to the repair queue.

### GPT-5.5 Judgement → Obligation Ledger Updates

**Gate**: Only on supervisor `go`. Ledger entries are appended (never mutated). Each entry must reference the capsule ID, PR URL, commit SHA, and supervisor judgement artifact.

### Obligation Ledger Updates → Learning Candidate Queue

**Gate**: A learning candidate is generated from the execution record and placed in the queue. **Learning candidates are never auto-applied.** Each candidate requires human or GPT-5.5 review before acceptance. The queue is append-only; rejection leaves the candidate in place with a rejection annotation.
