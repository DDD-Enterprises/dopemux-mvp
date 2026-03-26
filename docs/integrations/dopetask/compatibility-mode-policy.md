---
id: COMPATIBILITY_MODE_POLICY
title: Compatibility Mode Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Compatibility Mode Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Compatibility Mode Policy

## Purpose

Defines how the adapter handles legacy bundles that are missing one or more
canonical body fields. Compatibility mode prevents hard failures on older
engine output while making the degradation explicit and auditable.

## When Compatibility Mode Activates

Compatibility mode activates when `DopetaskCompatibilityMode.check()` detects
that the bundle is missing one or more fields from `CANONICAL_BODY_FIELDS`:

```
{status, summary, acceptance_checks, validation, artifacts, manifest}
```

Note: the `artifacts` field is also in `REQUIRED_FIELDS`, so its absence causes
a hard `BundleSchemaError` before compatibility mode is reached. Compatibility
mode only applies to the remaining five canonical fields.

## Normalization Rules

When a field is missing, the following defaults apply:

| Missing Field | Normalization |
|---------------|---------------|
| `status` | Defaulted to `"UNKNOWN"` |
| `acceptance_checks` | Defaulted to `[]` |
| `validation` | Defaulted to `{"outcome": "UNKNOWN", "gates": []}` |
| `summary` | Synthesized from `next_tactic` if present, else `""` |
| `manifest` | Synthesized from `generator` field if present, else `{"generator": "legacy_manifest", "version": "legacy"}` |

## Integration Flags Set

When compatibility mode activates:

```json
{
  "loaded_from": "compatibility_manifest",
  "compatibility_mode": true,
  "adapter_status": "DEGRADED",
  "warnings": [
    "Compatibility mode activated: missing canonical fields: ...",
    "Legacy manifest: missing field 'status' defaulted to 'UNKNOWN'.",
    ...
  ]
}
```

## Adapter Status in Compatibility Mode

Compatibility mode always results in `adapter_status = DEGRADED`, regardless
of archive presence. This is intentional: the caller must be informed that
the bundle is non-canonical and the result may be incomplete.

## Disabling Compatibility Mode

To enforce strict canonical validation (fail instead of degrade), use
`DopetaskBundleLoader.load_canonical()` before passing the bundle to the adapter,
or check `result.integration.compatibility_mode` and handle DEGRADED explicitly.

## Configuration

```yaml
bundle_loading:
  compatibility_mode: false  # Default: false — operators must opt in
```

When `compatibility_mode: false` (default), the adapter still runs compatibility
normalization but the DEGRADED status signals to callers that the bundle is
non-canonical.

## See Also

- `CANONICAL_BUNDLE_POLICY.md` — canonical bundle definition
- `READY_VS_DEGRADED_RULES.md` — full status decision table
