---
id: pm-plane-hub
title: PM Plane Hub
type: explanation
owner: '@hu3mann'
date: '2026-02-11'
prelude: PM Plane hub for evidence-first audit, minimal redesign, and task-packet
  implementation of the Dopemux PM / Task-Management plane
status: draft
author: '@hu3mann'
last_review: '2026-02-11'
next_review: '2026-05-12'
---
# PM Plane Hub

**Purpose**: Evidence-first audit, minimal redesign, and task-packet implementation of the Dopemux PM / Task-Management plane.

This plane follows strict phases. Do not skip phases.

## Templates (Authoritative)

- ADR template: `docs/90-adr/TEMPLATE_ADR.md`
- Task Packet template: `docs/task-packets/TEMPLATE_TASK_PACKET.md`

## How to Run

1. Open Claude Code in Supervisor Mode.
1. Paste: `docs/planes/pm/SUPERVISOR.md`
1. Execute Phase 0 commands locally and paste outputs back verbatim.
1. Produce deliverables into this folder.

## Phases and Deliverables

### Phase 0 (Inventory only, no design)

- PM_PLANE_INVENTORY.md
- PM_PLANE_GAPS.md

### Phase 1 (Friction + signal)

- PM_FRICTION_MAP.md
- SIGNAL_VS_NOISE_ANALYSIS.md

### Phase 2 (ADHD alignment)

- PM_ADHD_REQUIREMENTS.md
- PM_OUTPUT_BOUNDARIES.md

### Phase 3 (Minimal architecture)

- PM_ARCHITECTURE.md
- ADR-PM-### set (see ADR template)

### Phase 4 (Implementation)

- Task Packets A/B/C (see Task Packet template)

### Phase 5 (Derived workflows only)

- PM_WORKFLOWS_DERIVED.md
- PM_PRESETS.md (optional)
