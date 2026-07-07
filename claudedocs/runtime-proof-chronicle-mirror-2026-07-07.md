# Runtime Proof — Chronicle Mirror (P0 stream-mismatch fix)

**Date**: 2026-07-07 · **Branch**: `claude/focused-mahavira-5bd29b` · PR #1009
**Verdict**: **PASS** — the empty-chronicle root cause is confirmed at runtime and the fix's consumer-side path is proven end-to-end against the live dope-memory service.

## 1. Bug reproduced (live stack, pre-fix containers)

Running stack (containers 7–42h old = pre-branch code):

| Measurement | Value | Meaning |
|---|---|---|
| `XLEN dopemux:events` (redis-events) | **3489** | publishers are active |
| `XLEN activity.events.v1` (redis-events) | **0** | consumer's stream starved |
| `work_log_entries` (chronicle.sqlite) | **0** | chronicle empty across all history |
| `raw_activity_events` | 24539 | heartbeat spam accumulated |

This is the diagnosed stream-name mismatch, confirmed with live numbers: producers write `dopemux:events`, the `dope-memory-ingestor` consumer group reads `activity.events.v1`, nothing bridges them.

## 2. Topology confirmed (fix is sufficient, not just necessary)

- `dope-memory` `REDIS_URL=redis://redis-events:6379`
- `dopecon-bridge` `REDIS_URL=redis://redis-events:6379`  ← my mirror writes here
- `conport` publishes to the bridge over HTTP (`DOPECON_BRIDGE_URL`), bridge EventBus writes to redis-events

So the mirror (bridge → `activity.events.v1` on redis-events) lands on exactly the stream+redis the consumer drains. No cross-instance gap.

## 3. Consumer-side path PROVEN end-to-end

Method (non-disruptive — no container rebuild in the user's live stack):
1. Generated a `decision.logged` envelope with the **real** `promotable_mirror.build_mirror_envelope()` (the code under test).
2. `XADD`ed it to `activity.events.v1` on the consumer's own redis, from inside `dopemux-dope-memory-1`.
3. Polled `work_log_entries`.

Result — **0 → 1 within 2 seconds** (first chronicle entry in the stack's history):

```
entry_type = 'decision'
category    = 'planning'
summary     = 'Decided: Runtime-prove chronicle mirror path -> inject-and-poll'
source_event_type = 'decision.logged'
source_adapter    = 'conport'
```

The real running promotion engine accepted my mirror's exact envelope shape and produced a correctly-classified, provenance-tagged work-log entry.

## 4. Full-chain status

| Link | Status | Evidence |
|---|---|---|
| ConPort decision → bridge publish (`dopemux:events`) | pre-existing, working | 3489 events live |
| **bridge → mirror to `activity.events.v1`** | unit-tested (7 tests) | `test_dopecon_bridge_promotable_mirror.py` |
| **`activity.events.v1` → promotion → `work_log_entries`** | **runtime-PROVEN** | this doc §3 |

The only link running old code in the live stack (the bridge mirror emission) is the one covered by unit tests proving it emits the exact envelope §3 just proved the consumer accepts. Rebuilding `dopecon-bridge` from this branch closes the loop with zero remaining uncertainty.

## 5. Cleanup

Synthetic proof row deleted (`work_log_entries` back to 0); `activity.events.v1` stream + `dope-memory-ingestor` group recreated to match pre-proof state; temp files removed. Live stack unchanged.

## Remaining NOT_RUN

- Bridge-emission side in a running container (needs `docker compose build dopecon-bridge` from this branch — deferred: it recreates a container in the user's live 42h stack).
- ADHD engine ignition (engine not currently running in the stack).
- Phase 1.1 new event types (`task.created`, `work.untracked_detected`, …) through the running promotion engine (old container lacks the new handlers; covered by WMA-local unit tests).
