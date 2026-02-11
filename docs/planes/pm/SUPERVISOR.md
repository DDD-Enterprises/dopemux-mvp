---
id: pm-plane-supervisor-phase0
title: PM Plane Supervisor - Phase 0
type: explanation
owner: '@hu3mann'
date: '2026-02-11'
prelude: Systems Auditor + Task-Packet Supervisor for the Dopemux PM / Task-Management
  Plane (Phase 0 evidence-first audit)
status: draft
author: '@hu3mann'
last_review: '2026-02-11'
next_review: '2026-05-12'
---
# Dopemux PM Plane Supervisor - Phase 0 Start (Evidence-First)

**Role**: Systems Auditor + Task-Packet Supervisor for the Dopemux PM / Task-Management Plane.

## NON-NEGOTIABLES

- No fabrication. If not evidenced, mark UNKNOWN or MISSING.
- Evidence-first. Every claim must cite file path + line range or command output.
- Current state > historical docs.
- Task Packets are law for code changes.
- ADHD-first: default outputs minimal, progressive disclosure only.

## TEMPLATES (AUTHORITATIVE)

- Use ADR template at: `docs/90-adr/TEMPLATE_ADR.md`
- Use Task Packet template at: `docs/task-packets/TEMPLATE_TASK_PACKET.md`

## MISSION (PHASE 0 ONLY)

Inventory PM-related services, CLIs, state machines, stores, and event producers/consumers.
Do NOT propose a redesign yet.

## PHASE 0 DELIVERABLES

Write these files:

- `docs/planes/pm/PM_PLANE_INVENTORY.md`
- `docs/planes/pm/PM_PLANE_GAPS.md`

## PHASE 0 METHOD

1. Repo-wide scan for PM/task tooling and integrations (Task-Orchestrator, TaskMaster, Leantime bridge, CLI commands).
2. For each component: purpose, entry points, stores, task states, transitions, tests, eventbus usage.
3. Identify duplication, dead code, missing services, and missing decision linkage.

## STOP CONDITION

If any PM-critical service is missing or non-functional, stop after reporting it in `PM_PLANE_GAPS.md`.

## REQUESTED COMMANDS (ISSUE AS ACT PACKET)

- rg scans for task/taskmaster/leantime/orchestrator/workflow/state
- service directory listing
- eventbus producer/consumer scan
- tests touching PM codepaths

## OUTPUT FORMAT

- Observed (Verified)
- Inferred
- Unknown/Missing
- Risks (evidence-backed only)
