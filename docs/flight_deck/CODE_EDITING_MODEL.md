---
id: CODE_EDITING_MODEL
title: Code Editing Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Code Editing Model (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Code Editing Model

## Overview

The flight deck's code editing capability is governed by a strict 5-stage patch lifecycle.
No code change is applied without traversing the full pipeline.

## Patch Lifecycle

```
PLAN → DIFF → STAGE → [APPLY] → VERIFY → RECOMPUTE
```

### Stage 1: PLAN
- `PatchEngine.plan_patch()` constructs a `PatchPlan` with full provenance.
- Scope is defined: target files, optional regions, origin tactic, risk class.
- `classify_patch()` determines patch class from scope.

### Stage 2: DIFF
- `PatchEngine.render_diff()` produces human-readable diff with scope header.
- Diff is stored in `PatchPlan.diff_text`.
- Operator can inspect diff before any apply decision.

### Stage 3: STAGE
- All patches start in STAGED state.
- `SAFE_LOCAL_EDIT` and `SAFE_METADATA_EDIT` can auto-advance to APPLY when conditions allow.
- `SIGNOFF_REQUIRED_PATCH` remains STAGED until signoff packet is resolved.

### Stage 4: APPLY (Conditional)
- Requires: `APPLY_FIX` in `allowed_actions` AND posture in `{GO_SUPERVISED_ONLY, GO_FULL_AUTO}`.
- `DISALLOWED_PATCH` never reaches APPLY.
- `SIGNOFF_REQUIRED_PATCH` never reaches APPLY without explicit operator signoff.
- Outcome is one of: `APPLIED`, `STAGED`, `BLOCKED`, `FAILED`.

### Stage 5: VERIFY + RECOMPUTE
- Verification burden is matched to patch class (see PATCH_VERIFICATION_LINKAGE.md).
- After verification, gate recomputes posture and determines signoff/defer.
- `FusionEngine.fuse()` executes the full verify → gate → signoff/defer pipeline.

## Bounded Scope Definition

Every patch must define a bounded scope:
- `target_files`: Non-empty list of file paths. Empty list → DISALLOWED_PATCH.
- `target_regions`: Optional line ranges within files. Absence means whole-file scope.
- `cross_file`: Automatically derived as `len(target_files) > 1`.

Unbounded patches (no target files specified) are rejected before planning.
