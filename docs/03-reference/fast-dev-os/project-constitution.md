---
id: fast-dev-os-project-constitution
title: Fast Dev OS — Project Constitution
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Mission, scope, non-goals, vocabulary, and boundaries for the Fast Dev OS operational doctrine layer.
---
# Fast Dev OS — Project Constitution

## Mission

Accelerate `DDD-Enterprises/dopemux-mvp` design and implementation with the fewest operator actions while preserving repo truth, authority boundaries, task-packet discipline, and proof.

The default operating loop:

> **ChatGPT supervisor → one primary implementer → repo/GitHub/CI proof → optional reviewer only when risk earns it → Cockpit displays gates and UNKNOWNs.**

## Relationship to governance

This document **operationalizes** the governance layer at [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md); it **does not override** that layer. When this constitution and the governance layer conflict, the governance layer wins.

The authority matrix, label vocabulary (OBSERVED / CONFLICTING / UNKNOWN / RECOMMENDED), proof rules, and Codex control rules are defined by the governance layer. This constitution defines how those rules are applied in day-to-day operator workflow.

## Scope

In scope for the Fast Dev OS layer:

- Operational ledgers for current state (THREAD00 / PR / PACKET / PROOF snapshots).
- UNKNOWN/CONFLICTING/STALE register that carries forward [`AGENTS.md`](../../../AGENTS.md) §10 known dangers.
- Risk-routed lane taxonomy (L0–L6) for task assignment.
- Reusable prompt pack for multi-implementer workflow (Codex / Claude Code / Gemini / Grok / Jules / Copilot) — added by TP-DMX-FDOS-005.
- Reusable templates (Task Packet / Proof Bundle / PR body / validation library / runtime dependency cones) — added by TP-DMX-FDOS-006.
- Provenance documentation for external evidence bases (chat-context-v2 corpus).

## Non-goals

- **Not** an authority refresh of the governance layer (that lives in `docs/03-reference/governance/`).
- **Not** a runtime code change of any kind. The doctrine layer is docs-only.
- **Not** GitHub PR / CI enforcement (Phase 3 of the executive verdict; deferred).
- **Not** a Cockpit display layer (Phase 4 of the executive verdict; deferred). Cockpit is a display + gate + proof surface only — never PM, memory, execution, retrieval, or bridge authority.
- **Not** a schema extension to `dopetask-canonical-spec.json` (see RISK-SCHEMA in [`unknown-conflicting-stale.md`](unknown-conflicting-stale.md); deferred).
- **Not** a parallel-workstream launch (Phase 5 of the executive verdict; deferred).

## Vocabulary

Inherits the governance layer's label vocabulary (`OBSERVED`, `CONFLICTING`, `UNKNOWN`, `RECOMMENDED`) and adds operational labels:

- `SNAPSHOT-AT-<DATE>-HEAD-<SHA>` — marks a ledger as a point-in-time snapshot, not live truth.
- `NEEDS_LIVE_VALIDATION` — applied to any claim derived from chat extracts, snapshot ledgers, or external evidence bases.
- `STALE-RISK` — applied to volatile external tool capability claims that may have changed since recording.
- `BLOCKING` vs `NON-BLOCKING` — categorizes unresolved items by whether they prevent forward progress.

## Authority boundaries (inherited from AGENTS.md §6)

The Fast Dev OS layer must preserve, not collapse, the following split:

| System | Authority |
|--------|-----------|
| `dopemux` | Operator control, CLI, startup, routing, MCP/service coordination. |
| `dopetask` | External execution runtime via `scripts/dopetask`; `scripts/taskx` is compatibility shim. |
| `Leantime` | Passive PM metadata; project/ticket snapshots. |
| `task-orchestrator` | Workflow transitions and workflow views. |
| `ConPort` | Structured decisions, progress, project context, custom data. |
| `dope-memory` | Chronicle, historical receipts, evidence-preserving memory. |
| `dope-context` | Code/docs indexing and retrieval (derived evidence, not source truth). |
| `dopecon-bridge` | Adapter/proxy/event transport only — never canonical PM, workflow, decision, progress, chronicle, or retrieval authority. |
| `ADHD Engine` | Operator-support and cognitive-state surfaces only. |
| `Repo Truth Extractor` | Extraction/audit runtime only; outputs are evidence artifacts, not runtime truth. |
| `agents` | UNKNOWN runtime authority across `services/agents`, `src/dopemux/agent_orchestrator.py`, `services/task-orchestrator/task_orchestrator/agents` — do not promote without runtime proof. |
| `Cockpit/dopeUI` | Display + gate + proof surface only — never PM, memory, execution, retrieval, or bridge authority. |

## Risk-routed lane taxonomy

Used by operators to choose the right execution discipline for a given task. The taxonomy is **risk-routed**, not implementer-routed: any qualified implementer may run any lane if scope permits.

| Lane | Use when | Reviewer | Proof |
|------|----------|----------|-------|
| **L0: Design only** | No repo mutation | None | Citations + UNKNOWNs |
| **L1: Docs / prompt / packet** | Governance docs, prompt packs, task templates | Optional | diff, docs check, schema check |
| **L2: Bounded implementation** | Small source/test/config with clear owner | Default off | targeted tests, diff, precommit |
| **L3: Runtime spine** | CLI, dopetask, task-orchestrator, RTE, PM writes | Yes if risk ≥ medium | focused tests + integration proof |
| **L4: Boundary-sensitive** | PM, memory, retrieval, bridge, Cockpit gates, agents | Yes | boundary audit + tests |
| **L5: Security / provider / secrets** | Auth, secrets, CI, provider behavior, live extraction | Yes (security reviewer) | security scan + official docs |
| **L6: Parallel backlog** | Multiple independent low/medium packets | Spot review | branch matrix + PR checks |

This packet (TP-DMX-FDOS-004) is L1. So is TP-DMX-FDOS-005. TP-DMX-FDOS-006 is L2 (templates that downstream TPs must conform to — higher blast radius).

## Hard "nope" rules

Carried forward from the executive verdict §15:

1. No permanent multi-agent ceremony — reviewer only when risk earns it.
2. No dual implementer on one packet — one primary per TP.
3. No Cockpit execution authority — Cockpit is a display surface.
4. No bridge-as-truth — `dopecon-bridge` is adapter/proxy/event transport only.
5. No stale chat claims as `OBSERVED` — chat extracts are advisory; live repo evidence required for OBSERVED.
6. No implementation without packet — every TP must be schema-valid before any file write.
7. No merge without proof — every PR must have an AGENTS.md §9 PROOF.json.
8. No "done" without `VERIFIED` — final confidence requires evidence.

## Out of scope (deferred)

These belong to future packets:

- **Phase 3 (TP-DMX-FDOS-007-GITHUB-GATES)** — PR template enforcement, CI checks.
- **Phase 4 (TP-DMX-FDOS-008-COCKPIT-PROOF-GATES)** — Cockpit display layer.
- **Phase 5 (TP-DMX-WORKSTREAM-*)** — parallel backlog launch.
- **Schema extension** — adding `claude_code` and `jules` to `dopetask-canonical-spec.json` `execution.agent` enum.
- **Generator scripts** — automated snapshot-ledger refresh.
- **`docs/00-MASTER-INDEX.md` registration** — intrusive update; this packet defers it.
