---
id: ADR-PM-003-storage-derived-mirrored
title: Adr Pm 003 Storage Derived Mirrored
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-13'
last_review: '2026-02-13'
next_review: '2026-05-14'
prelude: Define PM storage boundaries so canonical task state is separate from telemetry and mirror projections.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
  - PM_ARCHITECTURE
  - ADR-PM-001-canonical-task-object
  - ADR-PM-002-pm-event-taxonomy
---
# Context

Current code shows multiple storage-adjacent surfaces:

- ConPort surfaces support decision and progress logging/retrieval through explicit client APIs.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L70-L210`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_shared_conport_client_client.py.txt:L66-L137`.
- Task-orchestrator telemetry is explicitly reported as suppression metrics and ADHD state snapshots.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L889-L929`.
- Integration paths project tasks into Leantime and other bridges.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/10_conport_search.txt:L58-L110`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_dopecon-bridge_dopecon_bridge_services_task_integration.py.txt:L125-L154`.

PM requires a strict boundary to remain Trinity-correct and avoid duplicate truth stores.

# Decision

PM adopts the following storage contract:

1. Canonical task state is PM-owned and written once per accepted transition.
2. ConPort stores decisions/progress as memory artifacts linked from canonical task records.
3. Chronicle stores high-signal mirrored events only; it is never canonical task authority.
4. Telemetry, suppression rates, and dashboards are derived views and cannot override canonical state.
5. Leantime/taskmaster sync surfaces are mirror/projection paths, not canonical authorities.

# Consequences

- Positive:
  - Eliminates split-brain ambiguity between lifecycle state and observability data.
  - Preserves Memory/Search boundary ownership.
  - Keeps PM default outputs minimal while allowing richer opt-in evidence paths.
- Tradeoffs:
  - Requires explicit link maintenance between canonical records and external mirrors.
  - Degraded-mode queue/retry contracts must be implemented carefully to remain idempotent.

# Alternatives Considered

1. Let telemetry become a fallback truth source when canonical writes fail.
- Rejected: violates deterministic state and introduces inferred truth.

1. Use ConPort progress store as full canonical PM task store.
- Rejected: ConPort remains memory plane authority, not PM lifecycle authority.

1. Mirror everything bidirectionally by default.
- Rejected: increases drift risk and ADHD cognitive load from conflict handling.

# Acceptance Tests

1. PM architecture doc contains a storage matrix separating Stored/Derived/Mirrored classes.
1. Telemetry is explicitly documented as non-canonical.
1. ConPort and mirror links are documented as references from canonical PM tasks.
1. UNKNOWN storage details are listed with evidence-needed statements.
