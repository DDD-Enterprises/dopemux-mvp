---
id: PM_PLANE_JULES_IMPLEMENTATION
title: Pm Plane Jules Implementation
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-21'
last_review: '2026-03-21'
next_review: '2026-06-19'
prelude: Pm Plane Jules Implementation (explanation) for dopemux documentation and
  developer workflows.
---
# PM Plane Jules Packet Implementation Plan

## Objective
Execute the PM-plane authority model implementation by safely dispatching Jules task packets in defined waves, ensuring each wave lands as a PR and is merged prior to progressing to the next wave. This leverages the existing `scripts/jules_submit_pm_plane_packets.py` tooling.

## Key Context
The overall project entails resolving the multi-source authority (Leantime, Task Orchestrator, ConPort, and dope-memory) according to the finalized PM-plane design documents. The implementation has been pre-segmented into detailed tasks specifically formatted for the "Jules" CLI.

## Execution Strategy

### Stage 1: Wave 0 (Baseline Ledger)
- **Target**: `PM-JULES-000`
- **Action**: Run `scripts/jules_submit_pm_plane_packets.py` to dispatch the first packet (`PM-JULES-000-baseline-ledger`).
- **Validation**: Monitor the repo for the created PR `codex/pm-jules-000-baseline-ledger`. Wait for it to be reviewed and merged into `main`.

### Stage 2: Wave 1 (Backend Authority Enforcement)
- **Target**: `PM-JULES-001`, `PM-JULES-010`, `PM-JULES-013`, `PM-JULES-015`, `PM-JULES-016`
- **Action**: Once Wave 0 is merged, use the Python script to submit the Batch B packets.
- **Validation**: Monitor for corresponding PRs.
- **Action**: Once Batch B PRs are merged, submit Batch C (`PM-JULES-011`, `PM-JULES-012`, `PM-JULES-014`) respecting their internal dependencies. Monitor and merge.

### Stage 3: Wave 2 (Adapter Narrowing)
- **Target**: Batch D (`PM-JULES-020`, `PM-JULES-021`, `PM-JULES-022`)
- **Action**: Dispatch Batch D in sequence upon verifying dependencies are successfully merged on `main`.

### Stage 4: Wave 3 (Integration, Readiness, Rollout)
- **Target**: Batch E (`PM-JULES-030`, `PM-JULES-031`, `PM-JULES-032`)
- **Action**: Dispatch the final batch to finalize E2E testing, CLI readiness, and rollout staging. Wait for PR creation and final merges.

## Notes & Constraints
- All PRs must target the `main` branch unless explicitly pulling from `dev`.
- A hard sequence MUST be strictly observed; Jules must not be fed new packets if previous dependency packets are unmerged.
- We will dry-run the `scripts/jules_submit_pm_plane_packets.py` tool (`--dry-run`) prior to active submissions.
