---
id: project-control-plane-architecture-validation
title: Project Control Plane Architecture Validation
type: reference
owner: '@hu3mann'
author: codex
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Fixture-only validation frame for a reusable Dopemux Project Control Plane substrate.
---
# Project Control Plane Architecture Validation

## Verdict

`ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS`

The reusable substrate shape is directionally correct: Dopemux owns generic control-plane contracts and dry-run artifact generation, while each project supplies profile and adapter configuration. dNh-CRM is the first adapter target, not the universal system.

The correction is important: this packet proves contract shape, ownership, fixture coverage, and dry-run handoffs. It does not prove a live exporter implementation. The verdict is scoped to contract-shape validation only; the read-only Opus audit returned `NEEDS_SUPERVISOR`, and Supervisor acceptance remains pending.

## Core Boundary

Dopemux Project Control Plane core owns:

- generic schemas
- project profile contract
- project evidence export contract
- red-lane result contract
- proof pointer contract
- dry-run Dopetask mapping contract
- dry-run Task Orchestrator item contract
- executor/audit/supervisor artifact contracts
- fixture harness conventions

Dopemux Project Control Plane core must not own:

- dNh CRM runtime behavior
- CRM, Telegram, calendar, identity, policy, event-store, or database writes
- GitHub mutation or merge authorization
- Task Orchestrator live writes
- Dopetask execution
- final audit or acceptance

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

- Dopetask mapping
- Task Orchestrator item/note rendering
- executor request/result
- audit request/result
- Supervisor decision draft

The E2E artifact at `reports/project-control-plane/validation/E2E_DRY_RUN_RESULT.json` records that no live writes, GitHub mutation, Dopetask execution, Task Orchestrator MCP write, or runtime imports occurred.

## Later Write Gates

Live writes require separate packets and explicit contracts:

- Task Orchestrator MCP writes require a write contract and replay/idempotency proof.
- Dopetask execution requires stable export and mapping contracts.
- dNh artifact-only export requires Supervisor acceptance of the generic substrate.
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
