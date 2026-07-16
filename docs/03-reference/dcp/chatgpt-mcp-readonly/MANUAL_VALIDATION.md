---
id: dcp-mcp-readonly-manual-validation
title: DCP Read-Only MCP Facade - Local V2 Validation Checklist
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Local-only manual validation checklist for the registry-v2 DCP read-only MCP evidence facade.
---
# Local V2 Validation Checklist

This checklist validates local stdio behavior only. It does not authorize a
tunnel, public listener, connector, provider account, credential, or live
backend call.

## Preconditions

- `DCP_FACADE_REGISTRY_V2` points to a local v2 registry with one enabled
  target that passes workspace and `.repo_id` checks.
- The automated local suite passes first:

  ```bash
  uv run --frozen pytest -q services/dcp-readonly-facade/tests
  ```

## Target and Local Evidence

| # | Action | Expected |
| --- | --- | --- |
| 1 | Call `list_targets()` | Only enabled opaque target IDs; no workspace path, URL, port, or runtime metadata. |
| 2 | Call `get_target_capabilities(target_id)` | Static policy list; every entry reports `live: "UNKNOWN"` and `callable: false`. |
| 3 | Call `get_target_repo_state_snapshot(target_id)` | Read-only branch, head SHA, and dirty state. |
| 4 | Call `list_target_proof_bundles(target_id)` | Bounded proof metadata only. |
| 5 | Call `fetch_target_proof_bundle(target_id, bundle_id)` | Containment-checked proof content with path and secret redaction. |
| 6 | Call `get_target_runtime_receipt(target_id)` | Redacted `UNKNOWN`/`BLOCKED` candidate states only; no endpoint and no callable state. |

## Fail-Closed Checks

| # | Action | Expected |
| --- | --- | --- |
| 7 | Call a target-scoped tool with an unknown opaque ID | `BLOCKED`, no evidence data. |
| 8 | Call with a path- or URL-shaped `target_id` | `BLOCKED`, `target_id: null`, and no reflected input. |
| 9 | Use `../` or a symlink escape as `bundle_id` | `BLOCKED`; no file outside the proof root is read. |
| 10 | Remove or corrupt the local catalog/runtime registry evidence | `PARTIAL`; receipt stays non-callable. |
| 11 | Inspect tool manifest | Only the six v2 tools are registered; no adapter, mutation, generic fetch, endpoint, or lifecycle tool exists. |

## Sign-off

- [ ] All local checks pass.
- [ ] No path, URL, port, secret, or operational topology appears in responses.
- [ ] No target receipt reports `callable: true`.
- [ ] No tunnel, connector, provider, live backend, or credential action ran.

Any failure in the fail-closed checks blocks further exposure work until a
separate authorized packet resolves it.
