---
id: OPERATOR_FLOW
title: Operator Flow
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operator Flow (explanation) for dopemux documentation and developer workflows.
---
# Operator Flow

## Overview

The adapter surfaces a three-panel operator interface:

1. **Header** — quick orientation (TP ID, posture, next action)
2. **Body** — full normalized adapter result
3. **Controls** — governance actions, signoff prompts

The `operator_view` sub-object in every `DopetaskAdapterResult` drives this flow.

---

## Panel 1: Mission Header

Rendered from `tp`, `posture`, and `summary`:

```
TP:           TP-PRMS-052  [VALIDATED]
Lane:         closed_loop (flight_deck)
Posture:      GO_SUPERVISED_ONLY
State:        SUPERVISED
Confidence:   HIGH  Risk: MEDIUM
Next Action:  Review engine output and apply approved fixes with signoff.
```

The header is always shown first. It is self-contained; an operator can act on the header
without opening any other panel.

---

## Panel 2: Body (Detail)

Opens `operator_view.open_first` — typically the bundle manifest:

```
proof/pr_merge/flight_deck/closed_loop/CLOSED_LOOP_MANIFEST.json
```

Then optionally `operator_view.open_second` — the archive:
```
proof/pr_merge/flight_deck/closed_loop.zip
```

Artifact priority order (`operator_view.artifact_priority`):
1. `bundle` — manifest/proof JSON (always available)
2. `supporting_artifacts` — trace, implicit action log, state reports
3. `archive` — zip (optional)

---

## Panel 3: Controls

Rendered from `governance`:

```
Allowed Actions:   [APPLY_FIX]  [MISSION_SUMMARY]
Blocked Actions:   [HIGH_RISK_AUTO_APPLY]

Signoff Required:  YES
Owner:             human_integrator
Reason:            Supervised posture requires explicit review
```

Controls are grayed out for items in `governance.blocked_actions`.

---

## Bundle-First Drill-Down Path

When a full bundle path is known:

```
DopetaskAdapter.from_bundle_path(path)
  → DopetaskBundleLoader.load(path)      # parse + validate
  → DopetaskStatusMapper.map_*()          # preserve governance semantics
  → DopetaskAdapterResult                 # normalized object
  → emit_adapter_artifacts(result, out)   # write ADAPTER_RESULT.json
```

No engine launch needed. The entire flow is read-only and deterministic.

---

## Launch-First Path

When only a TP ID is known (and a launcher is configured):

```
DopetaskAdapter.from_tp_id("TP-PRMS-052", context)
  → DopetaskPacketLauncher.launch("TP-PRMS-052", context)
       → FlightDeckOpsEngine + ClosedLoopEngine cycle
       → PacketLaunchTrace (bundle_path, success)
  → DopetaskBundleLoader.load(trace.bundle_path)
  → DopetaskStatusMapper.map_*()
  → DopetaskAdapterResult
```

If no launcher is configured, `from_tp_id` falls back to `find_bundle()` in `bundle_root`.

---

## Recommended Panel Logic

| posture.mode | recommended_panel |
|--------------|------------------|
| `GO_SUPERVISED_ONLY` | `"mission_header"` — operator needs to review before acting |
| `ADVISORY_ONLY` | `"mission_header"` — advisory only, no action controls shown |
| `HOLD` | `"detail"` — operator should drill into blockers |
| `DEFER_ONLY` | `"summary"` — deferred, nothing to act on immediately |
| `GO_FULL_AUTO` | `"summary"` — automation running, monitor summary |
| `LIVE_SAFE` | `"summary"` — safe automation, monitor summary |
| `UNKNOWN` | `"detail"` — investigate unknown state |
