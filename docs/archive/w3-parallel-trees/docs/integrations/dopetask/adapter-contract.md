---
id: ADAPTER_CONTRACT
title: Adapter Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Adapter Contract (explanation) for dopemux documentation and developer workflows.
---
# Adapter Contract

## Purpose

`DopetaskAdapter` is the single entry point for consuming Dopetask flight-deck outputs.
It returns a `DopetaskAdapterResult` — a normalized, immutable snapshot that downstream
tools, dashboards, and operators can consume without knowing internal proof folder layout.

---

## Entry Points

| Method | Input | Output |
|--------|-------|--------|
| `from_bundle_path(path)` | Path to manifest/bundle JSON | `DopetaskAdapterResult` |
| `from_tp_id(tp_id, context)` | TP ID string + optional context dict | `DopetaskAdapterResult` |

`from_tp_id` will launch the appropriate engine if a `DopetaskPacketLauncher` is configured,
otherwise falls back to finding an existing bundle in `bundle_root`.

---

## Normalized Object Contract

### Top-Level Fields

| Field | Type | Semantics |
|-------|------|-----------|
| `source` | str | Always `"dopetask"` |
| `schema_version` | str | `"1.0"` |
| `tp` | DopetaskTPIdentity | TP identifier and lifecycle state |
| `target` | DopetaskTarget | Repo, worktree, branch, PR |
| `posture` | DopetaskPosture | Operator control mode (never flattened) |
| `summary` | DopetaskSummary | Result, next action, confidence |
| `proof` | DopetaskProofRef | Bundle and archive file references |
| `governance` | DopetaskGovernance | Allowed/blocked actions, signoff |
| `operator_view` | DopetaskOperatorView | Where to look first |
| `integration` | DopetaskIntegration | Load metadata, errors, warnings |
| `computed_at` | float | Unix timestamp of adapter run |

### Field Semantics

**`posture.mode`** is a pass-through from the bundle. The adapter never remaps:
- `GO_SUPERVISED_ONLY` → remains `GO_SUPERVISED_ONLY` (not `READY`)
- `HOLD` → remains `HOLD` (not `BLOCKED`)
- `DEFER_ONLY` → remains `DEFER_ONLY`

**`summary.headline_state`** is a *derived* display label, not a governance signal:
- `GO_SUPERVISED_ONLY` → `SUPERVISED`
- `ADVISORY_ONLY` → `SUPERVISED`
- `HOLD` → `BLOCKED`
- `DEFER_ONLY` → `DEFERRED`
- `GO_FULL_AUTO` → `READY`
- `LIVE_SAFE` → `READY`

**`governance.signoff.required`** is set to `True` whenever `posture.signoff_required=True`.
It is NEVER set to `False` to "simplify" the output.

**`integration.adapter_status`** values:
- `READY` — bundle loaded, all required fields present
- `DEGRADED` — bundle loaded with warnings (e.g., missing archive)
- `ERROR` — fatal load failure; `integration.errors` contains details

---

## Invariants

1. `source` is always `"dopetask"`
2. `posture.mode` is always one of the 7 canonical values or `"UNKNOWN"`
3. `tp.status` is always one of the 8 canonical values or `"UNKNOWN"`
4. `governance.signoff.required` mirrors `posture.signoff_required` — never independent
5. `summary.next_action` is always a non-empty string
6. `integration.errors` is always a list (may be empty)
7. `computed_at` is always set (Unix float)

---

## Artifact Emission

`DopetaskAdapter.emit_adapter_artifacts(result, out_dir)` writes:
- `ADAPTER_RESULT.json` — full normalized object as JSON

This matches the pattern used by `ClosedLoopEngine`, `PatchEngine`, and `FusionEngine`.
