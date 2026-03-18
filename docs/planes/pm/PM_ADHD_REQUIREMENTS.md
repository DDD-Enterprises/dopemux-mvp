---
id: PM_ADHD_REQUIREMENTS
title: Pm Adhd Requirements
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-13'
next_review: '2026-05-12'
prelude: Pm Adhd Requirements (explanation) for dopemux documentation and developer
  workflows.
---
# PM ADHD Requirements (Phase 2)

Status: evidence-backed requirements locked for Phase 2.
Scope: contracts only; no PM architecture redesign.

## Observed failure modes (ADHD)

- Context loss: PM task flows still depend on remembering exact task IDs and fail closed (`Task {task_id} not found`) when IDs are lost after interruption; ADHD modules explicitly add context snapshot and restoration to reduce this failure mode. Evidence: `services/taskmaster/bridge_adapter.py:L148-L160`; `src/dopemux/cli.py:L2496-L2501`; `services/adhd_engine/domains/attention/context_preserver.py:L146-L182`; `services/adhd_engine/domains/task_enablement/working_memory_support.py:L6-L18`.
- Task pile-up: coordinator implements flood suppression for high-volume repeated events and overwhelm detection models rapid switching plus long no-progress windows as risk signals, showing pile-up is a first-class ADHD risk. Evidence: `services/task-orchestrator/event_coordinator.py:L428-L433`; `services/adhd_engine/domains/attention/overwhelm_detector.py:L6-L11`; `services/adhd_engine/domains/attention/overwhelm_detector.py:L118-L186`.
- Phase confusion: task status semantics are split across dialects (`pending/in_progress/completed/...` in orchestrator, `TODO/IN_PROGRESS/DONE/BLOCKED` in ConPort-facing client, and separate CLI status enum), increasing translation overhead across PM surfaces. Evidence: `services/task-orchestrator/task_orchestrator/models.py:L13-L21`; `services/task-orchestrator/conport_mcp_client.py:L85-L86`; `src/dopemux/adhd/task_decomposer.py:L31-L37`; `docs/planes/pm/PM_FRICTION_MAP.md:L21-L23`.
- False urgency: deep-focus suppression rules intentionally block lower-priority and non-interrupting events, and low-energy mode suppresses high cognitive-load events, which defines a concrete anti-urgency guardrail PM must preserve. Evidence: `services/task-orchestrator/event_coordinator.py:L410-L426`; `services/task-orchestrator/event_coordinator.py:L453-L471`; `services/task-orchestrator/tests/test_suppression_telemetry.py:L330-L345`.

## PM responsibilities vs Memory vs Search (Trinity)

| Plane | PM Phase 2 contract | Must not do |
|---|---|---|
| PM | Decide what action to show now, apply suppression policy, and expose minimal next-step output. Evidence: `services/task-orchestrator/event_coordinator.py:L385-L437`; `services/task-orchestrator/event_coordinator.py:L889-L929`. | PM must not persist full memory substrate or duplicate search pipeline internals. |
| Memory | Persist and restore working context, decisions, and interruption breadcrumbs that PM can reference. Evidence: `services/adhd_engine/domains/attention/context_preserver.py:L54-L62`; `services/adhd_engine/domains/task_enablement/working_memory_support.py:L150-L160`. | Memory must not own PM display policy or output suppression semantics. |
| Search | Produce evidence retrieval/scanning quality, including noise filtering in scans. Evidence: `docs/planes/pm/PM_FRICTION_MAP.md:L57-L63`. | Search must not own PM task-lifecycle semantics. |

## Minimum viable PM signals

PM default behavior MUST be driven by the smallest set of signals that supports action without overload:

- One actionable next step (`next_action`) plus current status summary. Evidence: `src/dopemux/adhd/workflow_manager.py:L211-L225`.
- Context recovery anchor (task, mental model, recent decisions) for interruption restart. Evidence: `services/adhd_engine/domains/attention/context_preserver.py:L171-L182`.
- Suppression snapshot (`events_received`, `events_passed`, `events_suppressed`, `suppression_rate_pct`) for signal/noise control. Evidence: `services/task-orchestrator/event_coordinator.py:L906-L913`.
- Overwhelm risk level from active attention signals. Evidence: `services/adhd_engine/domains/attention/overwhelm_detector.py:L31-L37`; `services/adhd_engine/domains/attention/overwhelm_detector.py:L95-L153`.

## Derived signals (no duplicated state)

Derived PM signals MUST come from telemetry or ADHD engine outputs, not from duplicated PM-local shadow state:

- `signal_noise_ratio` and `suppression_rate_pct` from suppression telemetry summary. Evidence: `services/task-orchestrator/event_coordinator.py:L893-L913`.
- `top_suppression_rule` from per-rule counters. Evidence: `services/task-orchestrator/event_coordinator.py:L914-L921`.
- Current ADHD operating state (`focus_mode`, `energy_level`, `context_switches`) from telemetry payload. Evidence: `services/task-orchestrator/event_coordinator.py:L924-L928`.
- Context restorable/not-restorable state from context snapshot availability. Evidence: `services/adhd_engine/domains/attention/context_preserver.py:L165-L170`; `services/adhd_engine/domains/attention/context_preserver.py:L171-L185`.

## Evidence index (Phase 2 bundle)

- Telemetry core: `docs/planes/pm/_evidence/PM-ADHD-02.outputs/nl_services_task-orchestrator_event_coordinator.py.txt`.
- Telemetry rationale and open measurement limits: `docs/planes/pm/_evidence/PM-ADHD-02.outputs/nl_services_task-orchestrator_SUPPRESSION_TELEMETRY.md.txt`.
- Telemetry tests: `docs/planes/pm/_evidence/PM-ADHD-02.outputs/nl_services_task-orchestrator_tests_test_suppression_telemetry.py.txt`.
- ADHD context and overwhelm surfaces: `docs/planes/pm/_evidence/PM-ADHD-02.outputs/nl_services_adhd_engine_domains_attention_context_preserver.py.txt`; `docs/planes/pm/_evidence/PM-ADHD-02.outputs/nl_services_adhd_engine_domains_attention_overwhelm_detector.py.txt`; `docs/planes/pm/_evidence/PM-ADHD-02.outputs/nl_services_adhd_engine_domains_task_enablement_working_memory_support.py.txt`.
- PM CLI surface: `docs/planes/pm/_evidence/PM-ADHD-02.outputs/nl_src_dopemux_cli.py.txt`.
- Supporting targeted scan: `docs/planes/pm/_evidence/PM-ADHD-02.outputs/10_adhd_pm_search.txt`.
