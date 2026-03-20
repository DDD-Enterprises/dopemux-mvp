---
id: INTEGRATION_MODEL
title: Integration Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Integration Model (explanation) for dopemux documentation and developer workflows.
---
# Dopetask Integration Model

## Overview

The Dopetask adapter layer exposes four surfaces for consuming Dopetask flight-deck proof
bundles and Task Packets (TPs) without manual folder archaeology.

---

## Surface 1: Packet (TP Identity)

A **Task Packet** is the unit of authorized work in Dopetask's flight-deck system. Each TP
has a canonical ID (`TP-PRMS-052`, `TP-PRMS-053`, `TP-PRMS-054`), a family (`flight_deck`),
a lane (`closed_loop`, `patch`, `fusion`), and a lifecycle status.

Relevant fields in the adapter object:
```
tp.id            — "TP-PRMS-052"
tp.family        — "flight_deck"
tp.lane          — "closed_loop" | "patch" | "fusion"
tp.title         — human-readable label
tp.status        — PLANNED | IN_PROGRESS | VALIDATED | OPERATIONAL | BLOCKED | DEFERRED | FAILED | UNKNOWN
tp.run_id        — ISO-8601 run timestamp
```

## Surface 2: Proof (Bundle Reference)

A **proof bundle** is the authoritative record produced by each engine run. It lives at
`proof/pr_merge/flight_deck/{lane}/` and contains a manifest JSON plus supporting artifacts.

Relevant fields:
```
proof.bundle_path       — absolute or relative path to manifest/bundle JSON
proof.bundle_present    — True if the file exists on disk
proof.archive_path      — optional .zip companion
proof.archive_present   — True if archive exists
proof.supporting_artifacts — list of additional JSON/log files
```

## Surface 3: Governance (Posture + Signoff)

**Posture** is the operator-level control mode set by the flight-deck. It is never flattened
or simplified by the adapter; semantics are preserved exactly.

```
posture.mode                    — GO_SUPERVISED_ONLY | HOLD | GO_FULL_AUTO | ADVISORY_ONLY | DEFER_ONLY | LIVE_SAFE | UNKNOWN
posture.advisory_only           — True only for ADVISORY_ONLY posture
posture.signoff_required        — True for GO_SUPERVISED_ONLY, ADVISORY_ONLY
posture.defer_only              — True for DEFER_ONLY
posture.auto_apply_allowed      — True for GO_FULL_AUTO, LIVE_SAFE, GO_SUPERVISED_ONLY
posture.auto_apply_risk_threshold — LOW | MEDIUM | HIGH

governance.allowed_actions      — actions permitted under current posture
governance.blocked_actions      — actions explicitly blocked
governance.signoff.required     — True/False (never flattened)
governance.signoff.owner        — who must sign off
governance.signoff.reason       — why signoff is required
```

**No-flatten rule**: `GO_SUPERVISED_ONLY` is never promoted to `READY`. `HOLD` is never
silently dropped. `signoff_required=True` is never coerced to False.

## Surface 4: Operator (UX Entry Points)

The **operator view** tells a human (or downstream tool) exactly where to look first and
what panel to open. It eliminates the need to know internal proof folder structure.

```
operator_view.open_first         — primary artifact to open (bundle manifest)
operator_view.open_second        — secondary artifact (archive)
operator_view.recommended_panel  — "mission_header" | "detail" | "summary"
operator_view.artifact_priority  — ordered list: ["bundle", "supporting_artifacts", "archive"]
```

The `summary.next_action` field provides a single human-readable instruction derived from
posture + status, requiring no further interpretation.
