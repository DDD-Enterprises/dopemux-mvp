---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-05-12'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# PM Plane

Purpose: Evidence-first audit, minimal redesign, and task-packet implementation of the Dopemux PM / Task-Management plane.

This plane is governed by strict phases. Do not skip phases.

## Non-negotiables
- No fabrication. If not evidenced, mark UNKNOWN or MISSING.
- Evidence-first. Every architectural claim must cite:
  - file path + line range, or
  - command output, or
  - explicit absence (0 hits + command).
- Current state > historical docs.
- Task Packets are law for code changes.
- ADHD-first. Default outputs are minimal; progressive disclosure only.
- Trinity boundaries: PM must not become a shadow Dope-Memory or DopeQuery store.

## How to run
1) Run Phase 0 evidence capture:
   - See: docs/planes/pm/_evidence/PM-INV-00.commands.txt
   - Paste outputs into: docs/planes/pm/_evidence/PM-INV-00.outputs/
2) Write Phase 0 deliverables:
   - docs/planes/pm/PM_PLANE_INVENTORY.md
   - docs/planes/pm/PM_PLANE_GAPS.md
3) Only after Phase 0 stop conditions clear:
   - Phase 1: PM_FRICTION_MAP.md
   - Phase 2: PM_ADHD_REQUIREMENTS.md + PM_OUTPUT_BOUNDARIES.md
   - Phase 3: PM_ARCHITECTURE.md + ADR-PM-### set
   - Phase 4: implementation via Task Packets
   - Phase 5: PM_WORKFLOWS_DERIVED.md (derived only)

## Phase 0 stop condition
If any PM-critical service is missing or non-functional, stop after documenting it in PM_PLANE_GAPS.md.
Do not proceed to Phase 1.

## Deliverables
- Phase 0:
  - PM_PLANE_INVENTORY.md
  - PM_PLANE_GAPS.md
- Phase 1:
  - PM_FRICTION_MAP.md
  - SIGNAL_VS_NOISE_ANALYSIS.md (create when Phase 1 begins)
- Phase 2:
  - PM_ADHD_REQUIREMENTS.md
  - PM_OUTPUT_BOUNDARIES.md
- Phase 3:
  - PM_ARCHITECTURE.md
  - ADR-PM-### set
- Phase 4:
  - Task Packets A/B/C
- Phase 5:
  - PM_WORKFLOWS_DERIVED.md
  - PM_PRESETS.md (optional)
