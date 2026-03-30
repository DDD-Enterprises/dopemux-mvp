---
id: PATCH_SCOPE_POLICY
title: Patch Scope Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Patch Scope Policy (explanation) for dopemux documentation and developer
  workflows.
---
# Patch Scope Policy

## Required Scope Elements

Every patch MUST specify:
1. `target_files` — non-empty list of file paths (absolute or repo-relative)
2. `risk_class` — one of `LOW`, `MEDIUM`, `HIGH`
3. `origin_tactic` — the tactic that triggered the patch
4. `rationale` — human-readable justification

Optional scope elements:
- `target_regions` — list of `{file, start_line, end_line}` dicts
- Absence of regions = whole-file scope (permitted but increases risk classification)

## Scope Rules by Risk Class

| Risk Class | Target Files | Regions | Cross-File | Resulting Patch Class |
|------------|-------------|---------|------------|----------------------|
| LOW, single file, non-meta | Required | Optional | No | SAFE_LOCAL_EDIT |
| LOW, single file, meta ext | Required | Optional | No | SAFE_METADATA_EDIT |
| LOW, multi-file | Required | Optional | Yes | LOW_RISK_PATCH_PROPOSAL |
| MEDIUM, single file | Required | Optional | No | LOW_RISK_PATCH_PROPOSAL |
| MEDIUM, multi-file | Required | Optional | Yes | SIGNOFF_REQUIRED_PATCH |
| HIGH, any | Required | Optional | Any | SIGNOFF_REQUIRED_PATCH |
| No target_files | — | — | — | DISALLOWED_PATCH |

## Cross-File Patch Requirements

Cross-file patches (`len(target_files) > 1`) require:
1. Enhanced verification: `CROSS_FILE_IMPACT_CHECK` added to check list
2. Elevated risk classification (at minimum LOW_RISK_PATCH_PROPOSAL)
3. Signoff if MEDIUM or HIGH risk

## Metadata File Extensions

Files with these extensions are classified as metadata for scope purposes:
`.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.ini`, `.md`

## Scope Invariants

1. Empty `target_files` → immediate DISALLOWED_PATCH, no further processing.
2. Scope cannot be expanded after `plan_patch()` is called.
3. Cross-file flag is derived, not operator-specified, to prevent gaming.
