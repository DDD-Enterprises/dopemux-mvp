---
id: ARCHIVE_DISCOVERY_POLICY
title: Archive Discovery Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Archive Discovery Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Archive Discovery Policy

## Purpose

Defines how the adapter discovers, validates, and reports the status of the
bundle archive (`.zip` file). Fixes the prior defect where absence of an archive
caused DEGRADED even when no archive was needed.

## Archive Expectation Rule

An archive is **expected** if and only if `bundle["artifacts"]` is non-empty.

```python
archive_expected = len(supporting_artifacts) > 0
```

Launcher-created bundles with `artifacts: []` do **not** require an archive.
The adapter will not emit an archive warning or set DEGRADED in this case.

## Archive Path Convention

The archive is expected at:

```
{bundle_path.parent.parent}/{bundle_path.parent.name}.zip
```

Examples:
- Bundle: `proof/pr_merge/flight_deck/closed_loop/MANIFEST.json`
- Archive candidate: `proof/pr_merge/flight_deck/closed_loop.zip`

## Resolution Outcomes

`DopetaskArchiveResolver.resolve()` returns an `ArchiveResolution`:

| `archive_expected` | zip exists | `archive_present` | `archive_path` | Note |
|--------------------|------------|-------------------|----------------|------|
| False | any | False | None | "No supporting artifacts; archive not expected." |
| True | True | True | path/to/zip | "Archive found: ..." |
| True | False | False | path/to/zip | "Archive not found: ..." |

## Effect on Adapter Status

| `archive_expected` | `archive_present` | Effect on `adapter_status` |
|--------------------|-------------------|---------------------------|
| False | any | No effect (READY if otherwise clean) |
| True | True | No effect (READY if otherwise clean) |
| True | False | Forces DEGRADED + warning in `integration.warnings` |

## DopetaskProofRef Update

The adapter updates `proof_ref.archive_present` with the resolved value.
When `archive_expected=False`, `archive_path` remains as the original
candidate path from `extract_proof_ref` (for auditing), but
`archive_present=False` is set explicitly.

## Configuration

```yaml
archive:
  expect_when_artifacts_present: true   # Archive expected only when artifacts[] non-empty
  fail_on_missing_expected: false        # DEGRADED (not ERROR) when expected archive absent
```

## See Also

- `CANONICAL_BUNDLE_POLICY.md` — canonical bundle definition
- `READY_VS_DEGRADED_RULES.md` — full status decision table
