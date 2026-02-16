---
id: PM_OUTPUT_BOUNDARIES
title: Pm Output Boundaries
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-13'
next_review: '2026-05-12'
prelude: Pm Output Boundaries (explanation) for dopemux documentation and developer
  workflows.
---
# PM Output Boundaries (Phase 2)

Status: default-minimal output contract locked for Phase 2.
Scope: documentation contract only; no CLI flag implementation in this packet.

## Default output (always minimal)

PM output MUST default to exactly three user-facing elements:

1. One-line summary of current PM state.
1. Next single recommended action.
1. Optional hint line: `Run --more for details`.

No additional tables, counters, or multi-step trees are shown by default.
Evidence basis for progressive minimality patterns: `src/dopemux/adhd/workflow_manager.py:L211-L234`.

## Progressive disclosure layers

Additional detail is opt-in and layered:

- `--more`: expanded context (top supporting signals, blockers, and current phase).
- `--why`: rationale trace (which rule or state produced the recommendation).
- `--evidence`: line-cited pointers to evidence artifacts and source lines.

This layering follows ADHD-oriented progressive disclosure already encoded in workflow components.
Evidence: `src/dopemux/adhd/workflow_manager.py:L211-L230`.

## Suppression rules (default behavior)

The PM surface defaults to suppression-first behavior where focus protection wins over verbosity:

- Suppress non-critical priorities in deep focus mode.
- Suppress non-interrupting events in deep focus mode.
- Suppress high cognitive-load events during low-energy state.
- Suppress event floods (more than 10 similar events in one minute).
- Always keep critical/high-safety events visible.

Evidence: `services/task-orchestrator/event_coordinator.py:L410-L433`; `services/task-orchestrator/event_coordinator.py:L453-L471`.

## What telemetry tracks (measurable now)

Current telemetry can measure:

- `events_received`, `events_passed`, `events_suppressed`.
- `signal_noise_ratio`, `suppression_rate_pct`, and runtime minutes.
- per-rule suppression volume (6 rules).
- per-event-type and per-priority received vs suppressed counts.
- active ADHD state attached to report (`focus_mode`, `energy_level`, `context_switches`).

Evidence: `services/task-orchestrator/event_coordinator.py:L96-L117`; `services/task-orchestrator/event_coordinator.py:L889-L929`; `services/task-orchestrator/tests/test_suppression_telemetry.py:L253-L289`; `services/task-orchestrator/tests/test_suppression_telemetry.py:L293-L322`.

## What is not yet measurable (UNKNOWN)

UNKNOWN items that must stay explicit until evidence exists:

- Historical suppression baselines and trends over time.
- Per-worker suppression attribution.
- Multi-cause suppression overlap accounting.

Evidence: `services/task-orchestrator/SUPPRESSION_TELEMETRY.md:L159-L165`; `services/task-orchestrator/tests/test_suppression_telemetry.py:L326-L345`.

## Trinity boundary guardrails

- PM may reference Memory outputs (context, breadcrumbs) but does not own memory persistence internals.
- PM may reference Search outputs (evidence pointers) but does not own search indexing/noise tooling internals.
- PM owns action selection and output suppression policy.

Evidence: `docs/planes/pm/PM_FRICTION_MAP.md:L39-L63`; `docs/planes/pm/SIGNAL_VS_NOISE_ANALYSIS.md:L105-L120`.

## Current CLI reality (for Phase 2 tracking)

Current `dopemux status` defaults to broad multi-panel output when no filters are supplied, and current options are domain panels (`--attention`, `--context`, `--tasks`, `--mobile`), not explicit `--more/--why/--evidence` tiers.
Evidence: `src/dopemux/cli.py:L2221-L2241`.
