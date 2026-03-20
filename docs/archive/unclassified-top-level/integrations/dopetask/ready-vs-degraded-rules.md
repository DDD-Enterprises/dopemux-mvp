---
id: READY_VS_DEGRADED_RULES
title: Ready Vs Degraded Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Ready Vs Degraded Rules (explanation) for dopemux documentation and developer
  workflows.
---
# READY vs DEGRADED Rules

## Purpose

Documents the complete decision table for `adapter_status` produced by
`DopetaskAdapter._build_result()`. Replaces the prior implicit rule
(any warning → DEGRADED) with an explicit, policy-driven table.

## Status Values

| Value | Meaning |
|-------|---------|
| `READY` | Bundle is canonical, archive situation is acceptable. Safe to proceed. |
| `DEGRADED` | Bundle loaded but with caveats (non-canonical or expected archive missing). Proceed with caution. |
| `ERROR` | Bundle could not be loaded or contains hard errors. Do not proceed. |

## Decision Table

| errors | is_canonical | arc_expected | arc_present | adapter_status |
|--------|-------------|--------------|-------------|----------------|
| yes | any | any | any | **ERROR** |
| no | True | False | any | **READY** |
| no | True | True | True | **READY** |
| no | True | True | False | **DEGRADED** |
| no | False | any | any | **DEGRADED** |

### Notes

- **errors**: Non-empty `integration.errors` list (load failure, schema error, launch failure).
- **is_canonical**: All canonical body fields present (checked by `DopetaskCompatibilityMode`).
- **arc_expected**: `len(bundle["artifacts"]) > 0` (checked by `DopetaskArchiveResolver`).
- **arc_present**: The expected `.zip` archive file exists on disk.

## Loaded From Labels

`integration.loaded_from` encodes the provenance of the bundle:

| Value | When set |
|-------|---------|
| `"launch"` | Bundle produced by `DopetaskPacketLauncher` in this session |
| `"canonical_bundle"` | Bundle loaded from disk and all canonical fields present |
| `"compatibility_manifest"` | Bundle loaded from disk but missing one or more canonical fields |
| `"bundle"` | Legacy/error fallback value (only in `_error_result`) |

## Relationship to Governance

`adapter_status` is an **adapter-layer** signal only. It does NOT affect:
- `posture.mode` (governance posture)
- `governance.allowed_actions` / `governance.blocked_actions`
- `summary.headline_state` (SUPERVISED / READY / BLOCKED / etc.)

These governance fields are derived solely from bundle content (posture + status),
not from the adapter loading quality. An adapter_status of DEGRADED does not
change the governance posture.

## Prior Defect — Fixed in TP-DMUX-ADAPT-002

Before this release:
- Any `proof_ref.archive_present = False` added a warning → DEGRADED
- Launcher bundles (`artifacts: []`) always triggered this → SEAMLESS_FLOW_VALIDATION was always DEGRADED
- Compatibility fallback was implicit (no `compatibility_mode` flag)

After this release:
- Archive warning only emitted when `archive_expected = True` and archive is absent
- `compatibility_mode` flag explicitly tracks compat path
- Status table is policy-driven, not warning-count-driven

## See Also

- `CANONICAL_BUNDLE_POLICY.md` — canonical bundle definition
- `COMPATIBILITY_MODE_POLICY.md` — compat mode behavior
- `ARCHIVE_DISCOVERY_POLICY.md` — archive resolution logic
