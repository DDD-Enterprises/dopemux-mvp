---
id: pm-task-orchestrator-leantime-followups
title: PM Task Orchestrator Leantime Followups
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
status: active
prelude: Follow-up queue for Task Orchestrator and Leantime integration work after canonical compose and authority ADR updates.
---
# Task Orchestrator + Leantime Follow-up Queue

This document tracks the immediate follow-up ticket set for PM-plane execution after the 2026-03-11 stack and ADR updates.

## Ticket Set

### PM-TO-001 - Standardize readiness contracts
- Scope: Align `/health` and workflow endpoint readiness criteria between task-orchestrator and leantime-bridge.
- Why: Operators need one stable readiness signal for promote/sync workflows.
- Acceptance criteria:
  - Runtime docs define readiness expectations for both services.
  - Integration tests fail if readiness contracts drift.

### PM-TO-002 - Promote warning propagation
- Scope: Ensure Leantime sync warnings emitted by task-orchestrator promotion are surfaced in CLI output and docs examples.
- Why: Promotions should degrade safely but visibly.
- Acceptance criteria:
  - Workflow docs include a warning-path example payload.
  - CLI output behavior is validated in tests.

### PM-TO-003 - Canonical port/runtime verification
- Scope: Validate lifecycle examples, bridge wiring, and tests against the observed task-orchestrator runtime default `3014` plus explicit `PORT` override behavior.
- Why: Prevent stale `8000` assumptions from drifting across docs, bridge config, and supervisor tooling.
- Acceptance criteria:
  - Active docs distinguish between task-orchestrator runtime default `3014` and any bridge/container assumptions still pointing at `8000`.
  - Validation covers both default and override behavior.

### PM-TO-004 - Rogue container remediation runbook
- Scope: Document and verify non-canonical task-orchestrator cleanup behavior in `scripts/start.sh`.
- Why: Prevent auto-restarting containers from old compose projects from shadowing the canonical stack.
- Acceptance criteria:
  - Runbook includes detection and cleanup behavior.
  - Ops validation demonstrates successful cleanup of rogue task-orchestrator containers.

### PM-TO-005 - PR docgen sync skill rollout
- Scope: Land the `pr-docgen-sync` core skill + Gemini/Copilot/Claude wrappers, sync installer wiring, and tests.
- Why: Ensure every PR/commit gets deterministic docs coverage and canonical index reconciliation.
- Acceptance criteria:
  - `templates/skills/pr-docgen-sync*/` exist and validate.
  - `scripts/skills/sync_repo_skills.py` installs both testgen and pr-docgen skill families.
  - Coverage tests exist for impact map, layout audit, and ticket-sync fallback behavior.

### PM-TO-006 - Live ticket sync verification against task-orchestrator
- Scope: Verify `update_progress` operation behavior from doc automation against a running orchestrator + Leantime setup.
- Why: Keep best-effort live sync path healthy and observable.
- Acceptance criteria:
  - Health probe + live sync behavior validated in local environment.
  - Fallback ledger behavior confirmed when orchestrator is unavailable.

## Progress Sync Log

- Timestamp: `2026-03-11T00:00:00Z`
- Baseline: `main...HEAD`
- Mode: `best-effort`
- Ticket `PM-TO-005`: `in_progress` (skill family implementation + docs/index reconciliation started)
- Ticket `PM-TO-006`: `pending` (requires live orchestrator environment verification)

## Related Decisions

- `docs/90-adr/adr-pm-plane-authority-boundaries.md`
- `docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md`
- `docs/90-adr/adr-dopecon-bridge-narrowing-to-adapter-only-role.md`
- `docs/90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md`

## Progress Sync Log
- Timestamp: `2026-03-11T19:09:17.367064+00:00`
- Baseline: `main...HEAD`
- Mode: `best-effort`
- Ticket `PM-TO-001`: `superseded` reason=`implemented in PR-INT-31` retry_after_utc=`2026-03-12T19:09:17.367064+00:00`
- Ticket `PM-TO-002`: `superseded` reason=`implemented in PR-INT-31` retry_after_utc=`2026-03-12T19:09:17.367064+00:00`
- Ticket `PM-TO-003`: `superseded` reason=`implemented in PR-INT-31` retry_after_utc=`2026-03-12T19:09:17.367064+00:00`
- Ticket `PM-TO-004`: `superseded` reason=`implemented in PR-INT-31` retry_after_utc=`2026-03-12T19:09:17.367064+00:00`
- Ticket `PM-TO-005`: `ledger-fallback` reason=`task-orchestrator unavailable` retry_after_utc=`2026-03-12T19:09:17.367064+00:00`
- Ticket `PM-TO-006`: `ledger-fallback` reason=`task-orchestrator unavailable` retry_after_utc=`2026-03-12T19:09:17.367064+00:00`

## Layout Audit Follow-up
- Timestamp: `2026-03-11T19:09:17.367344+00:00`
- Existing unrelated misplacements: `162`
- Findings report: `reports/docs-hygiene/pr-docgen-sync-layout-findings.json`
- Retry after UTC: `2026-03-12T19:09:17.367344+00:00`
- Pending remediation: `docs/02-how-to/docker-setup.md` type=`explanation` expected_prefixes=`docs/04-explanation/,docs/planes/,docs/03-reference/instructions/,docs/instructions/,docs/00-MASTER-INDEX.md,docs/INDEX.md,docs/03-reference/documentation-catalog.md,docs/03-reference/overview.md,docs/01-tutorials/overview.md,docs/02-how-to/overview.md`
- Pending remediation: `docs/02-how-to/deployment-worktree.md` type=`explanation` expected_prefixes=`docs/04-explanation/,docs/planes/,docs/03-reference/instructions/,docs/instructions/,docs/00-MASTER-INDEX.md,docs/INDEX.md,docs/03-reference/documentation-catalog.md,docs/03-reference/overview.md,docs/01-tutorials/overview.md,docs/02-how-to/overview.md`
- Pending remediation: `docs/02-how-to/install.md` type=`explanation` expected_prefixes=`docs/04-explanation/,docs/planes/,docs/03-reference/instructions/,docs/instructions/,docs/00-MASTER-INDEX.md,docs/INDEX.md,docs/03-reference/documentation-catalog.md,docs/03-reference/overview.md,docs/01-tutorials/overview.md,docs/02-how-to/overview.md`
- Pending remediation: `docs/02-how-to/installation-legacy.md` type=`explanation` expected_prefixes=`docs/04-explanation/,docs/planes/,docs/03-reference/instructions/,docs/instructions/,docs/00-MASTER-INDEX.md,docs/INDEX.md,docs/03-reference/documentation-catalog.md,docs/03-reference/overview.md,docs/01-tutorials/overview.md,docs/02-how-to/overview.md`
- Pending remediation: `docs/02-how-to/operations/adhd-engine-rollout.md` type=`explanation` expected_prefixes=`docs/04-explanation/,docs/planes/,docs/03-reference/instructions/,docs/instructions/,docs/00-MASTER-INDEX.md,docs/INDEX.md,docs/03-reference/documentation-catalog.md,docs/03-reference/overview.md,docs/01-tutorials/overview.md,docs/02-how-to/overview.md`
- Additional misplacements not listed inline: `157`

## Progress Sync Log
- Timestamp: `2026-04-01T00:00:00Z`
- Baseline: `main...HEAD`
- Mode: `ledger-only`
- Ticket `PM-TO-003`: `reopened` reason=`2026-04-01 authority evidence closure confirmed current task-orchestrator config default is 3014 while bridge config still defaults TASK_ORCHESTRATOR_URL to port 8000`
- Ticket `PM-TO-005`: `linked` artifact=`docs/05-audit-reports/supervisor-pm-mcp-server-matrix-2026-03-27.md`
- Ticket `PM-TO-005`: `linked` artifact=`docs/05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md`
- Ticket `PM-TO-005`: `linked` artifact=`docs/05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md`
- Ticket `PM-TO-005`: `linked` artifact=`docs/05-audit-reports/supervisor-pm-memory-authority-enforcement-packet-2026-04-01.md`
