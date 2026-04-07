---
id: PM_PHASE2_CLAIMS_LEDGER
title: Pm Phase2 Claims Ledger
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-13'
last_review: '2026-02-13'
next_review: '2026-05-12'
prelude: Phase 2 claims ledger for PM ADHD requirements and output boundaries.
---
# PM Phase 2 Claims Ledger

## Verified (Phase 2)

1) Suppression telemetry tracks lifetime event flow (`events_received`, `events_passed`, `events_suppressed`) plus per-rule, per-event-type, and per-priority counters. Evidence: `services/task-orchestrator/event_coordinator.py:L96-L117`; `services/task-orchestrator/event_coordinator.py:L389-L401`; `services/task-orchestrator/event_coordinator.py:L453-L471`.
2) PM can directly measure event-rate reduction via `suppression_rate_pct` and signal/noise via `signal_noise_ratio` in the suppression report summary. Evidence: `services/task-orchestrator/event_coordinator.py:L893-L913`; `services/task-orchestrator/SUPPRESSION_TELEMETRY.md:L148-L155`.
3) Telemetry report structure and metrics math are enforced by tests, including six-rule breakdown and zero-event edge behavior. Evidence: `services/task-orchestrator/tests/test_suppression_telemetry.py:L253-L289`; `services/task-orchestrator/tests/test_suppression_telemetry.py:L293-L322`.
4) ADHD context preservation is implemented as an explicit context capture/restore surface that returns task, mental model, active files, and recent decisions for interruption recovery. Evidence: `services/adhd_engine/domains/attention/context_preserver.py:L146-L185`.
5) ADHD overwhelm concepts are implemented in code with concrete signals (rapid switching, no progress, energy mismatch, break resistance, overwhelmed attention state). Evidence: `services/adhd_engine/domains/attention/overwhelm_detector.py:L6-L11`; `services/adhd_engine/domains/attention/overwhelm_detector.py:L118-L227`.
6) ADHD working-memory support is implemented with explicit challenge model, context breadcrumbs, interruption records, and fast thought capture. Evidence: `services/adhd_engine/domains/task_enablement/working_memory_support.py:L6-L19`; `services/adhd_engine/domains/task_enablement/working_memory_support.py:L86-L160`; `services/adhd_engine/domains/task_enablement/working_memory_support.py:L199-L214`.
7) Current PM-adjacent CLI status surface defaults to broad output (all panels on) and does not currently expose explicit disclosure-tier flags (`--more`, `--why`, `--evidence`) in this command. Evidence: `src/dopemux/cli.py:L2221-L2241`.

## Unknown (Phase 2)

- Whether end-to-end PM outputs in real user flows already satisfy the default-minimal contract (one-line summary, one next action, opt-in detail). Evidence needed: recorded PM CLI/session outputs from representative commands plus a contract conformance check against `PM_OUTPUT_BOUNDARIES.md`.
- Which single PM user-facing surface should canonically host `--more`, `--why`, and `--evidence` tiers without duplicating other planes. Evidence needed: command ownership matrix and invocation telemetry across `dopemux` PM-related commands.
- Historical suppression trend quality and baseline drift over time. Evidence needed: persisted telemetry store and time-series snapshots (hourly/daily) rather than runtime-only counters.
- Multi-cause suppression overlap rates (events matching multiple rules simultaneously). Evidence needed: non-short-circuited rule evaluation traces or dual-pass instrumentation for overlap accounting.
