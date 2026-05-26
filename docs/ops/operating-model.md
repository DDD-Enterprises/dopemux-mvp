---
id: ops-operating-model
title: DevOps AutoPR Operating Model
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Governance-first operating model for macro-packet, implementer, embedded audit, and PR Steward intake gates.
---
# DevOps AutoPR Operating Model

## Claim Posture

- OBSERVED: `AGENTS.md` requires repo-bound task packets, proof, validation, and explicit UNKNOWNs before finality.
- OBSERVED: `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` is the strict task-packet schema in this checkout.
- OBSERVED: `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, and `SERVICE_CATALOG.md` preserve split system authority.
- PROPOSED: This operating model defines the first governance slice for optimized development flow. It does not implement PR mutation or merge automation.

## Default Flow

1. GPT-5.5 Pro writes one macro-packet that includes scope, allowlist, validation, embedded-audit requirement, PR Steward intake requirement, and stop conditions.
2. One implementer executes the packet in a dedicated branch/worktree and preserves unrelated dirty state.
3. If the packet requires embedded audit, the implementer runs the proven local auditor invocation and captures the report in proof.
4. If a PR is opened, PR Steward v1 is the review-intake gate. It harvests GitHub state, classifies every review item, and emits `MERGE_READINESS.json`.
5. A second GPT-5.5 Pro supervisor review is skipped only when embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS` and PR Steward readiness is `READY`.
6. Escalation remains mandatory for blocked, unknown, high-risk, conflicting, or authority-boundary cases.

## Model Routing

| Role | Default Route | Gate |
| --- | --- | --- |
| Macro-packet supervisor | GPT-5.5 Pro | Must emit one bounded, schema-valid macro-packet. |
| Primary implementer | Codex or Claude Code through a repo-bound task packet | Must preserve allowlist, proof, and validation. |
| Embedded auditor | AGY/Antigravity Sonnet when invocation and model are locally proven; otherwise Claude Code Sonnet, Claude Code Opus, then Gemini CLI | Must write `AUDITOR_REPORT.md` or explicitly record `SKIPPED`. |
| PR review intake | PR Steward v1 check-only flow | Must classify every review/check/thread item and fail closed on UNKNOWN. |
| Second supervisor review | Skipped only after both gates are READY | Required when either gate is not READY. |

## Authority Boundaries

This model preserves these authority slices:

- `dopemux`: operator CLI, startup, routing, and MCP/service coordination.
- `dopetask`: external execution runtime through `scripts/dopetask`; `scripts/taskx` remains a compatibility shim.
- `task-orchestrator`: workflow transitions and workflow views.
- Leantime: passive PM metadata and project-ticket snapshots.
- ConPort: structured decisions, progress, context, and custom data.
- `dope-memory`: chronicle and evidence-preserving historical receipts.
- `dope-context`: code/docs indexing and retrieval.
- `dopecon-bridge`: adapter, proxy, and event transport only.
- ADHD Engine: operator support and cognitive-state surfaces only.
- Repo Truth Extractor: extraction and audit artifacts only.
- Agents: helpers unless a runtime path proves stronger authority.

## Escalation Triggers

Escalate to a human or supervisor when any of the following is true:

- embedded audit returns `FAIL` or unresolved `NEEDS_SUPERVISOR`
- PR Steward returns anything other than `READY`
- a reviewer or bot cannot be classified
- GitHub auth, PR state, CI state, or review thread state cannot be proven
- repo identity, branch identity, or task-packet schema alignment is unclear
- a requested change crosses PM, memory, retrieval, bridge, execution, ADHD, repo-truth, or agent authority boundaries
- implementation would require secrets, live provider calls, mutation of GitHub review state, merge queue mutation, or auto-merge behavior not explicitly authorized

## Non-Behavioral Status

`AUTO_APPLIED` may appear as a PR Steward disposition value. In this governance slice it is only a recorded status. It does not authorize automatic fixes, automatic review-thread resolution, merge queue mutation, or auto-merge.
