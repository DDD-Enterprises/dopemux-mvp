---
id: project-control-plane-architecture-validation
title: Project Control Plane Architecture Validation
type: reference
owner: '@hu3mann'
author: codex
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Fixture-only validation frame for reusable PCP Core substrate plus project extensions.
---
# Project Control Plane Architecture Validation

## Superseding Supervisor Framing

PCP Core is the reusable parent substrate for any Git repo. DCP is PCP Core plus the Dopemux extension. dNh CRM is PCP Core plus the dNh extension. Project-specific systems are extensions, not PCP Core.

This PR validates fixture and dry-run contract shape only. It does not implement or validate a generic runtime exporter. Negative cases remain fixture assertions, not executed behavior.

Dopetask and Task Orchestrator are Dopemux/DCP extension concepts. Any current PCP artifact that requires those named systems is a boundary defect to be repaired by the follow-up extension-contract and de-Dopemux boundary packets.

Architecture status: `PCP_CORE_FIXTURE_SHAPE_VALIDATED_RUNTIME_UNPROVEN`.

Merge status: draft; `NEEDS_SUPERVISOR`; not merge-ready.

## Verdict

`ARCHITECTURE_SHAPE_PLAUSIBLE_PENDING_EXPORTER`

PCP Core fixture and dry-run contract shape are directionally plausible. This packet proves contract shape, ownership, fixture coverage, and dry-run handoffs only. It does not prove a live exporter implementation or runtime behavior. The read-only Opus audit returned `NEEDS_SUPERVISOR`, and Supervisor acceptance remains pending.

Extension contract and generic authority-map schema are missing and require follow-up packets.

## Core Boundary

PCP Core owns:

- generic schemas
- project profile contract
- project evidence export contract
- red-lane result contract
- proof pointer contract
- executor/audit/supervisor artifact contracts
- fixture harness conventions

PCP Core must not require Dopemux, Dopetask, Task Orchestrator, DCP, dNh, OpenClaw, ConPort, dope-memory, dope-context, or any named project system.

PCP Core must not own:

- project runtime behavior (CRM, Telegram, calendar, identity, policy, event-store, or database writes)
- GitHub mutation or merge authorization
- final audit or acceptance

Dopemux/DCP extension surfaces (not PCP Core requirements):

- dry-run Dopetask mapping contract
- dry-run Task Orchestrator item contract
- Task Orchestrator live writes (blocked until write contract exists)
- Dopetask execution (blocked until mapping contract exists)

## Project Adapter Boundary

A project adapter owns configuration and evidence shape for one project:

- authority document paths
- active packet paths
- proof roots
- red-lane identifiers
- forbidden path patterns
- worktree constraints
- unknown/fail-closed behavior

Adapter configuration must not fork generic orchestration rules. If dNh knowledge cannot be represented in profile or adapter data, the architecture needs redesign before dNh implementation.

## Runtime Boundary

Project runtime remains outside PCP. For dNh, this includes CRM, Telegram, policy, event store, outbound channels, identity, and calendar surfaces. Runtime imports are forbidden in this validation packet and remain forbidden until a later packet explicitly authorizes them.

## Dry-Run Only

These surfaces are dry-run only in this packet:

- Dopemux/DCP extension: Dopetask mapping (fixture assertion only)
- Dopemux/DCP extension: Task Orchestrator item/note rendering (fixture assertion only)
- executor request/result
- audit request/result
- Supervisor decision draft

No generic PCP exporter is implemented in PR #925. No runtime exporter behavior is validated in PR #925.

The E2E artifact at `reports/project-control-plane/validation/E2E_DRY_RUN_RESULT.json` records that no live writes, GitHub mutation, Dopetask execution, Task Orchestrator MCP write, or runtime imports occurred.

## Build Order

1. PR925 framing/proof repair
2. PCP extension contract
3. PCP core de-Dopemux boundary repair
4. PCP generic exporter
5. DCP extension mapping
6. dNh extension mapping
7. fixture-to-runtime validation
8. PR Steward / proof readiness integration
9. Task Orchestrator visibility
10. live-write gates
11. FastAPI bridge / live writes last

## Later Write Gates

Live writes require separate packets and explicit contracts:

- Task Orchestrator MCP writes require a write contract and replay/idempotency proof (Dopemux/DCP extension).
- Dopetask execution requires stable export and mapping contracts (Dopemux/DCP extension).
- dNh artifact-only export requires Supervisor acceptance of PCP Core plus dNh extension mapping.
- FastAPI bridge work is last, after artifact, Dopetask, proof/status, and Task Orchestrator visibility adapters are proven.

## Never-Write Rules

The PCP core must never directly write:

- CRM/client/calendar/Telegram/OpenClaw/policy/identity/event-store surfaces
- runtime databases
- GitHub merge or branch-protection state
- proof acceptance or Supervisor ledger decisions
- Task Orchestrator live state before a write contract exists

## Validation Scope

This packet validates three project shapes:

- `reports/project-control-plane/fixtures/dnh_crm_fixture`
- `reports/project-control-plane/fixtures/dopemux_fixture`
- `reports/project-control-plane/fixtures/minimal_fixture`

The dNh and Dopemux fixtures prove asymmetry rather than fake uniformity. dNh carries file/path and runtime red lanes. Dopemux carries split-authority and governance-plane red lanes. The minimal fixture proves UNKNOWN handling without project-specific defaults.
