---
id: SIGNAL_VS_NOISE_ANALYSIS
title: Signal Vs Noise Analysis
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: ADHD-first event classification for PM plane distinguishing actionable signals from cognitive noise.
---
# Signal vs Noise Analysis (Phase 1, Critiqued)

Status: Tightened for citation integrity, evidence quality tagging, and Trinity boundaries.
Evidence roots: `docs/planes/pm/_evidence/PM-FRIC-01.outputs/`; `docs/planes/pm/_evidence/PM-TELEM-01.outputs/`

## Signal Events (Show by Default)

Events that require developer attention or action. Each citation verified against evidence files.

| Signal | Why It Is Signal | Evidence Quality | Evidence |
|---|---|---|---|
| Task status transitions (`in_progress`, `completed`, `blocked`) \| Coordinator routes these values to dedicated handlers. `blocked` triggers focus-suggestion emission to help user pivot. \| Direct code \| `nl_...event_coordinator.py.txt L400-L407` (status routing); `nl_...event_coordinator.py.txt L674-L683` (blocked handler emits focus suggestion) |
| High and critical priorities under deep-focus gating | Deep-focus mode explicitly passes only CRITICAL and HIGH events. Non-critical interruptions blocked. | Direct code | `nl_...event_coordinator.py.txt L48-L55` (EventPriority enum: CRITICAL=1 through BACKGROUND=5); `nl_...event_coordinator.py.txt L331-L338` (deep focus filter) |
| ADHD break reminders and context-switch detection | Event schema explicitly models `break_reminder` and `context_switch` as distinct state types. These are time-sensitive and non-batchable by design. \| Direct code \| `nl_...events_types.py.txt L73-L77` (ADHDEvent.StateType enum) |
| Task creation tool calls from wrapper | Wrapper emits creation event for `create_task`, `parse_prd`, `decompose_task`. These represent new work items entering the system. \| Direct code \| `nl_...server.py.txt L185-L191` (emit_task_event on creation tools) |
| Energy-level gating of high-cognitive-load events | When `current_energy_level == "low"`, coordinator suppresses events with `cognitive_load > 0.7`. This is an active signal rule — its activation changes what the developer sees. \| Direct code \| `nl_...event_coordinator.py.txt L340-L344` (energy-level filter) |

## Noise Events (Suppress by Default)

Events that are implementation details, confirmations of user-initiated actions, or non-PM concerns.

| Noise | Why It Is Noise for PM Triage | Evidence Quality | Evidence |
|---|---|---|---|
| Binary `__pycache__` matches in grep evidence \| Not actionable PM semantics. Inflate triage stream with compilation artifacts. \| Scan hit \| `30_memory_burden_search.txt L2,L9-L11` (binary file matches) |
| Non-PM `HealthStatus` hits from `health.py` \| Regex matches contain `status=` tokens but describe system monitoring, not task lifecycle. \| Scan hit \| `20_friction_search.txt L81-L96` (health.py HealthStatus.CRITICAL/WARNING) |
| CLI `progress.add_task(...)` progress-meter calls \| Rich progress UI plumbing. Not PM ownership boundaries or task-state contracts. \| Scan hit \| `20_friction_search.txt L1098-L1114` (15+ progress.add_task calls for Restoring/Saving/Starting UI spinners) |
| Theme/visual transition events | Energy-state theme interpolation is automatic and non-actionable. | Direct code | `nl_...events_types.py.txt L85-L97` (ThemeEvent: switched/updated/interpolated) |
| Routine session lifecycle events | `attached`, `detached`, `pane_created`, `layout_changed` are expected tmux mechanics, not PM state changes. \| Direct code \| `nl_...events_types.py.txt L100-L115` (SessionEvent actions) |
| Routine worktree operations | `created`, `removed`, `cleaned` confirm user-initiated actions. Only `switched` is signal (triggers context recovery). \| Direct code \| `nl_...events_types.py.txt L36-L50` (WorktreeEvent actions) |

## Suppression Rules

### Rule 1: Priority-based filtering (always active)

Suppress events with `priority == LOW` or `priority == BACKGROUND` unless explicitly subscribed.
Evidence: `[Direct code] nl_...event_coordinator.py.txt L48-L55` (EventPriority: CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4, BACKGROUND=5).

### Rule 2: Deep-focus gating (when `current_focus_mode == "deep"`)

Pass only CRITICAL and HIGH events. Block non-critical interruptions.
Evidence: `[Direct code] nl_...event_coordinator.py.txt L331-L338`.

### Rule 3: Energy-level gating (when `current_energy_level == "low"`)

Suppress events with `cognitive_load > 0.7` to prevent overwhelm during low-energy states.
Evidence: `[Direct code] nl_...event_coordinator.py.txt L340-L344`.

### Rule 4: Event flood protection (always active)

When >10 similar events fire within one minute, log flood warning and suppress duplicates.
Evidence: `[Direct code] nl_...event_coordinator.py.txt L346-L349` (flood detection threshold).

### Rule 5: Batch-eligible event coalescing

Events marked `can_batch=True` in ADHDMetadata should be coalesced into periodic digests rather than delivered individually. Events with `time_sensitive=True` bypass batching.
Evidence: `[Direct code] nl_...event_bus.py.txt L34-L38` (ADHDMetadata: interruption_allowed, focus_required, time_sensitive, can_batch).

### Rule 6: Evidence audit noise suppression

During PM evidence triage, suppress binary-cache grep rows and non-PM status matches unless running an explicit cross-plane audit.
Evidence: `[Scan hit] 30_memory_burden_search.txt L2,L9-L11`; `20_friction_search.txt L81-L96`.

### Rule 7: Citation integrity gate

Any event classification without a verifiable evidence citation is invalid and must be moved to the Open Questions section as UNKNOWN.

## Telemetry Reality Check (As Implemented)

### What PM can now measure

- Event-rate reduction is now directly measurable as `suppression_rate_pct`, with `signal_noise_ratio` computed from pass/receive counts.
Evidence: `[Direct code] nl_services_task-orchestrator_event_coordinator.py.txt L889-L912`; `[Direct code] nl_services_task-orchestrator_tests_test_suppression_telemetry.py.txt L293-L310`.

- PM can attribute suppression volume to six concrete rules (`custom_filter`, `deep_focus_priority`, `deep_focus_interrupt`, `energy_level`, `flood`, `expiry`).
Evidence: `[Direct code] nl_services_task-orchestrator_event_coordinator.py.txt L104-L110`; `L914-L921`; `[Direct code] nl_services_task-orchestrator_tests_test_suppression_telemetry.py.txt L282-L289`.

- PM can segment suppression by event type and priority (received vs suppressed) for current runtime.
Evidence: `[Direct code] nl_services_task-orchestrator_event_coordinator.py.txt L393-L401`; `L463-L471`; `L922-L923`.

- PM can read telemetry through both periodic logs and health endpoint payloads.
Evidence: `[Direct code] nl_services_task-orchestrator_event_coordinator.py.txt L254-L271`; `L957-L972`; `[Direct code] nl_services_task-orchestrator_tests_test_suppression_telemetry.py.txt L349-L362`.

### What PM still cannot measure (yet)

- Long-horizon suppression trends (hourly/daily), historical baselines, and persisted telemetry history are not yet implemented and remain listed as future work.
Evidence: `[Direct code] nl_services_task-orchestrator_SUPPRESSION_TELEMETRY.md.txt L157-L162`.

- Per-worker suppression attribution is not yet implemented.
Evidence: `[Direct code] nl_services_task-orchestrator_SUPPRESSION_TELEMETRY.md.txt L164`.

- Multi-cause suppression overlap is not measurable because suppression is short-circuited at first matching rule.
Evidence: `[Direct code] nl_services_task-orchestrator_event_coordinator.py.txt L403-L433`; `[Direct code] nl_services_task-orchestrator_tests_test_suppression_telemetry.py.txt L327-L345`.

## Trinity Boundaries (PM vs Memory vs Search)

### PM-owned signal rules

Task lifecycle orchestration (status routing, blocked-task intervention) and deep-focus/energy event gating logic.
Evidence: `[Direct code] nl_...event_coordinator.py.txt L400-L407` (status routing); `nl_...event_coordinator.py.txt L331-L344` (focus + energy gating).

### Memory-derived friction surfaces

Conflict queuing and missing-field validation behavior surfaced via ConPort/adapter code paths. The *detection* is Memory-owned; the *user-facing friction* is PM-owned.
Evidence: `[Scan hit] 30_memory_burden_search.txt L8` (manual resolution); `30_memory_burden_search.txt L12-L21` (missing-field checks).

### Search-owned noise artifacts

Binary-cache matches and broad-regex false positives are evidence-tooling quality concerns. They inflate PM triage but are not PM-domain friction.
Evidence: `[Scan hit] 30_memory_burden_search.txt L2,L9-L11`; `20_friction_search.txt L81-L96`.

## Open Questions

### What is the measured event-rate reduction after these suppression rules?

Partially resolved (runtime-only). The report now exposes `suppression_rate_pct` and `signal_noise_ratio`, but historical trend telemetry is still future work.
Evidence: `[Direct code] nl_services_task-orchestrator_event_coordinator.py.txt L889-L912`; `[Direct code] nl_services_task-orchestrator_SUPPRESSION_TELEMETRY.md.txt L157-L162`.

### Which suppressed event classes are still needed for incident recovery?

UNKNOWN. Evidence needed: user validation and incident replay after suppression is applied.

### Which PM notifications must stay visible in deep-focus mode by policy?

UNKNOWN. Evidence needed: explicit PM policy document mapping event classes to focus-mode behavior. Current code implements CRITICAL+HIGH passthrough but no policy rationale is documented.

### What is the optimal batch window for ADHD event coalescing?

UNKNOWN. Evidence needed: A/B testing of batch intervals (1min vs 5min vs 15min). The `can_batch` flag exists in code but no coalescing implementation or interval tuning was found.
