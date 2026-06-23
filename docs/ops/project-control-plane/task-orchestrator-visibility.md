---
id: PCP-TO-VISIBILITY
title: PCP Core Task-Orchestrator Projection-Only Visibility
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: PCP Core Task-Orchestrator Projection-Only Visibility (explanation) for dopemux
  documentation and developer workflows.
---
# PCP Core Task-Orchestrator Projection-Only Visibility

## Overview

This document describes the **READ/PROJECTION-ONLY** mapping of Task-Orchestrator state
(items + dependencies) into PCP evidence.

**Hard constraints — enforced in code:**

- There is NO MCP write path of any kind.
- The projection is NOT proof, PM-metadata, merge authority, or live-write authority.
- `is_proof` is always `False`.
- `authority` is always `"NONE"`.
- `mcp_write_performed` is always `False`.

Module: `src/dopemux/pcp/task_orchestrator_projection.py`

---

## What the Projection Is

The projection is a **read-only snapshot** of Task-Orchestrator state, shaped for
consumption by downstream PCP evidence pipelines. It records what was observed at a
point in time and nothing more.

Downstream packets **may consume** this projection as a read view. They **must never**:

- treat it as proof,
- treat it as a merge authority,
- use it to drive PM-metadata writes, or
- pass it to any write surface.

---

## Projection Fields

| Field | Type | Value |
|---|---|---|
| `schema_version` | string | `"pcp.to_projection.v0"` |
| `surface_class` | string | `"PROJECTION"` — never `"PROOF"` |
| `is_proof` | bool | Always `False` |
| `authority` | string | Always `"NONE"` |
| `mcp_write_performed` | bool | Always `False` (const-style sentinel) |
| `source_truth_refs` | list of string | The `source_ref` passed at projection time |
| `generated_at` | ISO 8601 string | Timestamp of projection assembly |
| `items` | list of objects | Read-only subset: `id`, `title`, `role`, `depth`, `status_label` |
| `dependencies` | list of objects | Read-only subset: `from_id`, `to_id`, `type` |

---

## The Fail-Closed No-Write Guard

`forbid_mcp_write(tool_name)` enforces read-only access at the tool boundary.

**Rules (evaluated in order):**

1. If `tool_name` is in `_WRITE_TOOLS` → raise `ProjectionWriteForbidden`.
2. If `tool_name` is NOT in `_READ_TOOLS` → raise `ProjectionWriteForbidden` (unknown = deny).
3. Return `None` only for explicitly recognised read tools.

The **default for anything unknown is DENY** — unknown tool names are never permitted.

### Write tools (always denied)

| Tool name |
|---|
| `manage_items` |
| `advance_item` |
| `manage_notes` |
| `manage_dependencies` |
| `claim_item` |
| `complete_tree` |
| `create_work_tree` |

### Read tools (explicitly permitted)

| Tool name |
|---|
| `query_items` |
| `query_dependencies` |
| `query_notes` |
| `get_context` |
| `get_blocked_items` |
| `get_next_item` |
| `get_next_status` |

---

## Injectable Harvest

`harvest_projection(*, source_ref, generated_at, runner)` provides a thin read-only
harvest wrapper. The `runner` parameter is **required** — no default live MCP call is
made. If `runner` is `None`, `NotImplementedError` is raised immediately.

Runners must call only read tools. The module cannot enforce this at the runner
boundary, but `forbid_mcp_write` is available for runners to self-validate.

**Testing pattern:** supply a fake runner that returns canned data. No live MCP
calls are made in tests.

```python
def fake_runner(*, source_ref: str) -> dict:
    return {
        "items": [{"id": "abc", "title": "T", "role": "leaf",
                   "depth": 1, "status_label": "queue"}],
        "dependencies": [],
    }

result = harvest_projection(
    source_ref="workspace:/path",
    generated_at="2026-06-22T00:00:00Z",
    runner=fake_runner,
)
assert result["is_proof"] is False
assert result["authority"] == "NONE"
```

---

## Relationship to PCP Evidence

The projection sits at the **read layer** of the PCP evidence pipeline:

```
Task-Orchestrator (source of truth)
        |
        | read-only (query_items, query_dependencies)
        v
project_orchestrator_state()  ← pure function, no mutation
        |
        | projection dict (is_proof=False, authority=NONE)
        v
Downstream PCP evidence consumers
        |
        | may READ the projection
        | must NOT treat it as proof or write authority
        v
(proof assembly lives elsewhere — separate module, separate authority)
```

The projection is a **read view**, not a truth surface. Downstream packets that need
to assert proof must obtain proof from a dedicated proof-assembly path, not from this
module.

---

## Validation Invariants

The test suite (`tests/project_control_plane/test_to_projection.py`) asserts:

- `is_proof` is `False` and `authority` is `"NONE"` on every projection.
- Write tool names appear only in the `_WRITE_TOOLS` frozenset definition, never as
  function call invocations in the module source.
- `forbid_mcp_write` raises `ProjectionWriteForbidden` for all 7 write tools.
- `forbid_mcp_write` raises `ProjectionWriteForbidden` for any unrecognised tool name.
- `forbid_mcp_write` returns `None` for all explicitly recognised read tools.
- Input lists are not mutated by `project_orchestrator_state`.
- `ValueError` is raised on malformed input (non-list, empty `source_ref`, missing `id`).
