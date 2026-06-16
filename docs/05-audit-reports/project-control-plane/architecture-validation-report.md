---
id: project-control-plane-architecture-validation-report
title: Project Control Plane Architecture Validation Report
type: reference
owner: '@hu3mann'
author: codex
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Fixture-only architecture validation report for TP-DMX-PCP-ARCHITECTURE-VALIDATION-0001.
---
# Change Summary

Created fixture-only validation artifacts for `TP-DMX-PCP-ARCHITECTURE-VALIDATION-0001`. The packet demotes dNh RDCP from universal system to first project adapter target, adds strict PCP contracts, adds three fixture packs, and records a dry-run E2E chain without live writes.

# Authority Used

- `AGENTS.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_GPT55.md`
- `docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md`
- `docs/ops/operating-model.md`
- `docs/ops/pr-steward.md`
- `docs/ops/pr-action-bridge.md`
- `docs/ops/embedded-audit.md`

# Evidence Reviewed

Repo truth confirms Dopemux already has DCP schemas, PR Steward schemas, proof schemas, Task Orchestrator surfaces, and strict task-packet validation. The primary checkout was dirty, so this packet was executed in a dedicated clean worktree from current `origin/main`.

# Architecture Verdict

`ARCHITECTURE_CONFIRMED_WITH_CORRECTIONS`

The substrate should be generic PCP core plus project adapters. This verdict is scoped to contract-shape validation only: schemas, ownership boundaries, fixture packs, and dry-run artifacts. The read-only Opus audit returned `NEEDS_SUPERVISOR`, so Supervisor adjudication is still required before acceptance. A real generic exporter and dNh live artifact-only exporter require later packets.

# Ownership Matrix

See `docs/ops/project-control-plane/ownership-matrix.md`.

Pass posture:

- Every listed responsibility has one primary owner.
- Shared responsibilities are expressed as handoff contracts.
- Only Supervisor owns acceptance.
- Only Dopetask/Codex executor lanes own execution.
- Project runtime writes remain owned by project runtime under gated packets.

# Contracts Added

- `schemas/project_control_plane/project_profile.schema.json`
- `schemas/project_control_plane/project_evidence_export.schema.json`
- `schemas/project_control_plane/project_red_lanes.schema.json`
- `schemas/project_control_plane/dopetask_packet_mapping.schema.json`
- `schemas/project_control_plane/proof_pointer.schema.json`
- `schemas/project_control_plane/orchestrator_item.schema.json`
- `schemas/project_control_plane/executor_run_request.schema.json`
- `schemas/project_control_plane/executor_run_result.schema.json`
- `schemas/project_control_plane/audit_request.schema.json`
- `schemas/project_control_plane/audit_result.schema.json`
- `schemas/project_control_plane/supervisor_decision.schema.json`

All schemas use JSON Schema syntax, explicit enums, explicit `UNKNOWN` states where applicable, and `additionalProperties: false`.

# Fixtures Added

- `reports/project-control-plane/fixtures/dnh_crm_fixture`
- `reports/project-control-plane/fixtures/dopemux_fixture`
- `reports/project-control-plane/fixtures/minimal_fixture`

Each fixture includes a project profile, evidence export, red-lane classification, and negative cases. Fixture data is fake or placeholder-only and contains no secrets.

# Dry-Run Result

See `reports/project-control-plane/validation/E2E_DRY_RUN_RESULT.json`.

The dry-run chain is:

1. project profile
2. project evidence export
3. red-lane classification
4. Dopetask packet mapping dry-run
5. proof pointer
6. Task Orchestrator note item dry-run
7. audit request
8. supervisor decision draft

No live writes, GitHub mutation, Dopetask execution, Task Orchestrator MCP write, runtime imports, or dNh runtime changes are claimed.

# Negative Tests

Every adversarial fixture assertion blocks or escalates. These are fixture expectations, not executable classifier results:

- missing active packet -> `BLOCKED_UNKNOWN_ACTIVE_PACKET`
- dirty old dNh checkout -> `BLOCKED_FORBIDDEN_WORKTREE`
- runtime file touched -> `NEEDS_SUPERVISOR`
- `data/*.sqlite3` included -> `BLOCKED_RUNTIME_DB`
- CRM write surface detected -> `NEEDS_SUPERVISOR`
- Task Orchestrator live write requested too early -> `BLOCKED_NO_WRITE_CONTRACT`
- invalid schema -> `BLOCKED_SCHEMA_INVALID`
- unknown proof freshness -> `NEEDS_EVIDENCE_REFRESH`
- open Dopemux PR used as authority -> `BLOCKED_UNACCEPTED_AUTHORITY`

# Validation Performed

Validation is recorded in `proof/TP-DMX-PCP-ARCHITECTURE-VALIDATION-0001/PROOF.json`.

# Proof Artifacts

- `task-packets/generated/TP-DMX-PCP-ARCHITECTURE-VALIDATION-0001.json`
- `reports/project-control-plane/validation/E2E_DRY_RUN_RESULT.json`
- `proof/TP-DMX-PCP-ARCHITECTURE-VALIDATION-0001/PROOF.json`
- `proof/TP-DMX-PCP-ARCHITECTURE-VALIDATION-0001/AUDITOR_REPORT.md`

# Risks / Drift

- No live generic exporter implementation is included.
- Read-only Opus audit returned `NEEDS_SUPERVISOR`; Supervisor acceptance is not recorded.
- Negative fail-closed cases are asserted fixture expectations, not executed classifier results.
- Task Orchestrator live writes and Dopetask execution remain blocked.

# Forbidden Action Confirmation

- Live Task Orchestrator written: false
- Dopetask executed: false
- GitHub mutated: false
- dNh runtime changed: false
- CRM written: false
- Telegram sent: false
- Calendar written: false
- Identity changed: false
- Policy changed: false
- Runtime DB changed: false
- Branch protection changed: false

# Rollback Plan

Revert the packet branch or remove only the files listed in the task packet allowlist. No external state was mutated.

# Decision Request

Request Supervisor adjudication of the `NEEDS_SUPERVISOR` audit result. If accepted or accepted with corrections, the next implementation packet should build the generic fixture-based exporter before any dNh live artifact-only exporter.
