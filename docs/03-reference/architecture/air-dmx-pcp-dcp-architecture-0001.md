---
id: AIR-DMX-PCP-DCP-ARCHITECTURE-0001
title: PCP Core / DCP / dNh Architecture Intent Record
type: reference
owner: '@hu3mann'
author: codex
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: Build-planning architecture intent record for PCP Core substrate and project extensions.
---

> **Status:** ACCEPTED_FOR_BUILD_PLANNING
> **Runtime authority:** No
> **Use:** Build sequencing and task-packet governance
> **Supersedes:** DCP-as-parent framing for PCP/DCP work
> **Blocks:** generic exporter before extension contract and de-Dopemux boundary repair

# AIR-DMX-PCP-DCP-ARCHITECTURE-0001

## Authority Notice

This AIR is a build-planning record, not runtime proof. Runtime code, config, compose wiring, tests, active entrypoints, and live GitHub state outrank this document (AGENTS.md §2). If runtime evidence conflicts with this AIR, runtime wins. If PR evidence conflicts with this AIR for a specific PR, current PR/GitHub evidence wins for that PR.

## 1. Status

| Field | Value |
|---|---|
| AIR_STATUS | ACCEPTED_FOR_BUILD_PLANNING |
| CAN_WRITE_TASK_PACKETS_FROM_THIS_AIR | YES_WITH_LIMITS |

Task packets may be written from this AIR for framing repair, extension contract, authority-map schema, de-Dopemux boundary repair, exporter planning, extension mapping, validation, PR Steward readiness, Task Orchestrator projection, and live-write gate contracts. They may not claim runtime PCP acceptance until runtime exporter and negative-trap proofs exist.

## 2. Decision Summary

**PROPOSED:** PCP Core is the reusable project-control substrate for any Git repository.

**PROPOSED:** DCP / Dopemux Control Plane is PCP Core plus the Dopemux extension, not the parent of PCP.

**PROPOSED:** dNh CRM control plane is PCP Core plus the dNh extension, not the architecture template.

**PROPOSED:** Any future project-specific control plane is PCP Core plus a project extension.

**OBSERVED_BY_FILE:** The current repository is a composed multi-system workspace with operator control, execution handoff, PM, memory, retrieval, bridge/proxy, ADHD support, and repo-truth extraction split across different systems rather than unified into one authority surface.

**OBSERVED_BY_FILE:** PR #925 is salvageable but not merge-ready because current generic PCP artifacts still contain Dopemux-specific Dopetask and Task Orchestrator surfaces, and because generic extension and authority-map contracts are missing.

**OBSERVED_BY_PROOF:** PR #925 validates fixture/dry-run shape only; it does not prove a generic runtime exporter, generic repo runtime behavior, executed negative traps, DCP extension mapping, or dNh live adapter readiness.

**BLOCKED:** The generic exporter must not be built before extension contract and boundary repair because `project_evidence_export.schema.json` is structurally Dopemux-shaped and fixture-locked.

**BLOCKED:** Live writes, Dopetask execution, Task Orchestrator MCP writes, dNh runtime mutation, Action Bridge mutation, and FastAPI bridge implementation are out of sequence.

## 3. Architecture Tree

```
PCP Core
  generic repo discovery
  generic project identity
  generic project profile
  generic authority map
  generic evidence export
  generic red-lane policy and engine
  generic proof/status pointer model
  generic validation and dry-run harness
  generic negative-case runner
  generic extension contract
  generic exporter
  baseline no-extension operation
Extensions
  Dopemux / DCP extension
  dNh CRM extension
  Other project extensions
Planes
  Execution Plane
  Audit Plane
  Proof Plane
  Workflow / Projection Plane
  Runtime Boundary
  Live-Write Gates
```

PCP Core owns generic contracts and fail-closed mechanics only. Extensions are additive project profiles. Task Orchestrator is projection-only, not PCP proof truth. Live-write gates remain BLOCKED until explicit canonical writer, approval, idempotency, rollback, audit, and post-write verification exist.

## 4. PCP Core Definition

| Capability | Current repo status | Build packet |
|---|---|---|
| Generic repo discovery | UNKNOWN / MISSING | TP-DMX-PCP-CORE-GENERIC-EXPORTER-0001 |
| Generic project identity | PARTIAL | TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001 |
| Generic project profile | PARTIAL | TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001 |
| Generic authority map | MISSING | TP-DMX-PCP-EXTENSION-CONTRACT-0001 |
| Generic evidence export | CONFLICTING | TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001 |
| Generic red-lane engine | PARTIAL | TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001 |
| Generic proof/status pointer | PARTIAL | TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001 |
| Generic validation harness | PARTIAL | TP-DMX-PCP-FIXTURE-TO-RUNTIME-VALIDATION-0001 |
| Generic negative-case runner | MISSING / ASSERTED_ONLY | TP-DMX-PCP-FIXTURE-TO-RUNTIME-VALIDATION-0001 |
| Generic extension contract | MISSING | TP-DMX-PCP-EXTENSION-CONTRACT-0001 |
| Generic exporter | MISSING | TP-DMX-PCP-CORE-GENERIC-EXPORTER-0001 |
| Baseline no-extension operation | UNKNOWN | TP-DMX-PCP-CORE-GENERIC-EXPORTER-0001 |

## 5. Extension Contract (Proposed Keystone)

`extension_manifest.schema.json` and `authority_map.schema.json` must be designed together as co-keystones (packet 2). Extensions may contribute authority-map entries, red lanes, evidence paths, proof/status mappings, and adapters. Extensions must not weaken core fail-closed behavior, proof gates, audit gates, or promote bridges/proxies to authority. Extensions must not require Dopemux, dNh, OpenClaw, Task Orchestrator, Dopetask, or any named system for baseline PCP operation.

## 6. PR #925 Disposition

| Field | Value |
|---|---|
| PR925_STATUS | KEEP_DRAFT_PENDING_CORE_REPAIR |
| PR925_MERGE_READY | NO |
| PR925_NEXT_REPAIR | TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002 |

Preserve fixture packs, candidate core schemas, DCP materials as extension inputs, dNh fixtures as extension inputs, and proof/audit contracts. Repair overstrong labels, keep NEEDS_SUPERVISOR, and re-scope first repair to remaining items only. Move Dopetask/Task Orchestrator schemas to DCP extension namespace in later packets. Do not mark PR #925 READY.

## 7. Build Sequence

1. PR #925 framing/verdict/thread/PAL repair
2. Extension contract + authority_map schema
3. PCP Core de-Dopemux boundary repair
4. Generic exporter on plain Git repo
5. DCP extension mapping
6. dNh extension mapping
7. Fixture-to-runtime negative-trap execution
8. PR Steward proof-readiness integration
9. Task Orchestrator visibility, projection-only
10. Live-write gates, contracts only
11. FastAPI bridge / live writes last

Contract/boundary before exporter. Extensions after core. Validation before live gates. FastAPI/live writes last.

## 8. Red Lines

- No live writes before live-write gates
- No Dopetask execution in PCP Core validation
- No Task Orchestrator MCP write before write contract
- No dNh runtime mutation
- No generic exporter before extension contract and boundary repair
- No `ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS` for fixture-only evidence
- No PR #925 READY with unclassified review items or unresolved blocking threads
- No bridge/proxy/mirror promoted to authority

## 9. Next Packet

**NEXT_PACKET_ID:** TP-DMX-PCP-PR925-FRAMING-PROOF-REPAIR-0002

Repair PR #925 framing/proof posture only: downgrade overstrong verdicts, preserve NEEDS_SUPERVISOR, classify outdated/unresolved review threads, record PAL codereview/precommit as NOT_RUN, state PCP Core is parent and DCP/dNh are extensions. Do not redo `after_sha` orphan or dNh `policy_ref` repairs from `68b8fd17`; verify instead.

**Then:** co-design TP-DMX-PCP-EXTENSION-CONTRACT-0001 and TP-DMX-PCP-CORE-DEDOPEMUX-BOUNDARY-0001.

## 10. Final Summary

- PCP Core = reusable project-control substrate for any Git repo
- DCP / Dopemux Control Plane = PCP Core + Dopemux extension
- dNh CRM control plane = PCP Core + dNh extension
- Project-specific control plane = PCP Core + project extension

**Highest risk shortcut:** building the generic exporter against the current Dopemux-shaped, fixture-locked core schema.

**Highest leverage simplification:** one parent substrate, one extension contract, one authority map, one generic exporter, then project extensions.
