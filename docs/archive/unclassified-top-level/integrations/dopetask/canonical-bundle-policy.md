---
id: CANONICAL_BUNDLE_POLICY
title: Canonical Bundle Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Canonical Bundle Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Canonical Bundle Policy

## Purpose

Defines what constitutes a canonical Dopetask proof bundle and how the adapter
distinguishes canonical bundles from legacy (compatibility) manifests.

## Canonical Bundle Definition

A bundle is canonical when ALL of the following are true:

1. **ID field present** — `tp_id` or `pr_id` (or `id`) exists at the top level.
2. **`artifacts` field present** — may be an empty list.
3. **All canonical body fields present**:
   - `status`
   - `summary`
   - `acceptance_checks`
   - `validation`
   - `manifest`

When all conditions are met, the adapter sets `loaded_from = "canonical_bundle"` and
`compatibility_mode = False`.

## Strict Canonical Load

Use `DopetaskBundleLoader.load_canonical(path)` when you require strict canonical
validation. This method raises `BundleSchemaError` with the message
`"Bundle missing canonical fields: ..."` if any of the above body fields are absent.

This is appropriate for automated pipelines where a non-canonical bundle indicates
an upstream engine defect that must be surfaced as an error rather than silently
tolerated.

## Adapter Behavior — Canonical Path

| Condition | `loaded_from` | `compatibility_mode` | `adapter_status` |
|-----------|--------------|----------------------|-----------------|
| Canonical, no archive needed | `canonical_bundle` | `False` | READY |
| Canonical, archive expected + present | `canonical_bundle` | `False` | READY |
| Canonical, archive expected + absent | `canonical_bundle` | `False` | DEGRADED |

## Generator Responsibility

Engines (ClosedLoopEngine, PatchEngine, FusionEngine) must emit bundles with all
canonical fields populated. Missing fields in engine output indicate a defect in
the emitting engine.

## Enforcement

- `DopetaskBundleLoader.REQUIRED_FIELDS` — hard required (load fails if absent)
- `DopetaskBundleLoader.EXPECTED_FIELDS` — canonical expected (missing → compat mode)
- `DopetaskCompatibilityMode.CANONICAL_BODY_FIELDS` — cross-checks at adapter level

## See Also

- `COMPATIBILITY_MODE_POLICY.md` — behavior when canonical fields are absent
- `READY_VS_DEGRADED_RULES.md` — status decision table
