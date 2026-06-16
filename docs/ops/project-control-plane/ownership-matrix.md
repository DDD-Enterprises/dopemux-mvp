---
id: project-control-plane-ownership-matrix
title: Project Control Plane Ownership Matrix
type: reference
owner: '@hu3mann'
author: codex
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Fixture-only ownership matrix for TP-DMX-PCP-ARCHITECTURE-VALIDATION-0001.
---
# Project Control Plane Ownership Matrix

Claim posture: this matrix is a validation artifact, not acceptance. Runtime code, task packets, schemas, and proof artifacts remain stronger authority than this document.

| Component | Current implementation surface | Owns | Must not own | Inputs | Outputs | Persistence | Mutation risk | Generic or project-specific |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task Orchestrator MCP | MCP workflow/item/note surface; session context says queue/work/review/terminal roles | Workflow visibility, notes, item presentation | Proof truth, execution truth, acceptance, project runtime writes | Dry-run item payloads, proof pointers | Human-facing work graph projection | MCP/store-owned state, not PCP truth | High if live writes happen before write contract | Generic projection |
| Task Orchestrator FastAPI service | `services/task-orchestrator/**` and docs under `docs/03-reference/systems/task-orchestrator` | Coordination API and future cockpit bridge when proven | PCP evidence truth or Supervisor acceptance | Workflow models, API requests | HTTP workflow views | Service database/state when running | High if treated as authority | Generic service, not core PCP |
| Dopetask | `scripts/dopetask`; canonical packet schema | Packet execution, series state, proof lifecycle | Safety policy, Supervisor acceptance, dNh runtime behavior | Task packets, allowlists, validation commands | Execution receipts, proof bundles | Packet/proof artifacts | High if execution is invoked too early | Generic execution lane |
| RDCP layer | DCP/RDCP architecture artifacts and future exporter contracts | Evidence export, red-lane classification, repair planning, adapter contracts | Running work, merging PRs, live project writes | Project profiles, fixture exports, proof pointers | Local evidence exports and dry-run plans | PCP-owned local artifacts | Medium; should be artifact-only now | Generic core plus adapter boundary |
| PR Steward | `docs/ops/pr-steward.md`, `schemas/pr_steward/**`, `tools/pr_steward` | Check-only PR intake, readiness classification | GitHub mutation, proof authorship, acceptance | PR state snapshots, proof, embedded audit | Readiness JSON and ledgers | Local proof/review bundle artifacts | Medium if readiness is mistaken for acceptance | Generic PR review gate |
| Action Bridge | `docs/ops/pr-action-bridge.md`, `schemas/pr_action_bridge/**`, `tools/pr_action_bridge` | Pure repair/action plan compilation | Applying fixes, GitHub mutation, acceptance | PR Steward artifacts | `ACTION_PLAN.json`, repair packet text | Caller-owned output directory | Low while pure/dry-run | Generic compiler |
| Proof system | `proof/**`, `schemas/proof/**`, proof docs | Evidence records, validation outputs, freshness data | Supervisor acceptance, runtime truth, hidden success | Commands, outputs, hashes, validation status | `PROOF.json`, auditor reports | Appendable proof directories | Medium if stale proof is accepted | Generic with shape-family adapters |
| Codex runner | Bounded implementation in this worktree | Investigation, minimal edits, validation, proof production | Final audit, readiness, acceptance, merge authorization | Active packet, repo truth, fixtures | Diffs, proof, final report | Git branch/worktree | High if scope expands | Generic implementer |
| Audit router | `docs/ops/embedded-audit.md`, audit schemas | Auditor route selection and audit request shape | Implementation, merge, acceptance | Proof bundle, target artifacts | Audit request/result artifacts | Proof/audit artifacts | Medium if self-certification occurs | Generic audit lane |
| Supervisor ledger | Human/Supervisor decision outside Codex | Acceptance, red-lane override, merge authorization | Repo mutation | Proof, audit, readiness artifacts | Acceptance or rejection decision | Ledger outside this packet | High if bypassed | Generic authority |
| Project adapter | Project profile and fixture pack under `reports/project-control-plane/fixtures/**` | Repo-specific paths, red lanes, authority docs, proof locations | Generic orchestration rules | Project profile, fixture evidence | Project evidence export | Fixture/config artifacts | Medium if project logic leaks into core | Project-specific |

## Handoff Contracts

- Task Orchestrator receives dry-run item payloads only until a write contract exists.
- Dopetask receives packet mappings only after export schema stability; this packet performs no execution.
- PR Steward and Action Bridge may inform repair planning but cannot authorize mutation.
- Proof pointers expose freshness and validation state; they do not collapse auditor verdict into validation status.
- Supervisor acceptance is separate from Codex, audit, proof, PR Steward, and Task Orchestrator outputs.
