# Auditor Report — TP-DMX-PR-ACTION-BRIDGE-006

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-26
**TP**: TP-DMX-PR-ACTION-BRIDGE-006 — PR Action Bridge compiler
**Status**: PASS_WITH_RISKS (all HIGH findings resolved; MEDIUM findings resolved)

---

## Scope

Files reviewed:

- `tools/pr_action_bridge/compiler.py`
- `schemas/pr_action_bridge/action_plan.schema.json`
- `tests/pr_action_bridge/test_compiler.py`
- `docs/ops/pr-action-bridge.md`

---

## Findings

### F-006-HIGH-1 — Action IDs non-sequential when unknown blockers are skipped

**Severity**: HIGH
**Status**: RESOLVED

`compile_action_plan()` used `enumerate(blockers)` to generate action IDs
(`action-{idx+1:04d}`). When an unrecognized blocker appeared between two
recognized ones, the emitted IDs would be gapped (e.g., `action-0001`,
`action-0003`), contradicting the "sequential ID" intent and breaking
downstream consumers that rely on contiguous IDs.

**Fix applied**: Introduced a separate `action_num` counter that only
increments on recognized blockers. IDs now stay sequential regardless of
unknown blockers in the list.

**Test added**: `test_ids_stay_sequential_when_unknown_blocker_between_known`
confirms `action-0001` / `action-0002` even with an unknown blocker between.

---

### F-006-MED-1 — `compile()` shadows Python built-in

**Severity**: MEDIUM
**Status**: RESOLVED

The public function was named `compile`, shadowing Python's built-in
`compile()`. No behavioral impact in this module, but increases cognitive
load and makes REPL debugging error-prone.

**Fix applied**: Renamed to `compile_action_plan`. Tests import via
`compile_action_plan as compile` for readability.

---

### F-006-MED-2 — Silent coercion to placeholder values hides malformed inputs

**Severity**: MEDIUM
**Status**: RESOLVED

`pr_number = int(merge_readiness.get("pr_number") or 0)` and
`repo = str(... or "")` silently produced `pr_number=0` / `repo=""` when
callers passed malformed input. Schema validation downstream would catch it,
but the error location was misleading.

**Fix applied**: Explicit `KeyError` raised for missing required keys
(`pr_number`, `repo`, `readiness`) before any field access. Tests added for
all three cases.

---

### F-006-LOW-1 — Unknown blockers silently skipped without documentation

**Severity**: LOW
**Status**: RESOLVED

Forward-compatibility behavior (unknown blockers skipped) was undocumented.

**Fix applied**: Added inline comment in the skip branch explaining the
rationale. Test `test_unknown_blocker_is_silently_skipped` locks the behavior.

---

### F-006-LOW-2 — Empty string item IDs could resolve ambiguously

**Severity**: LOW
**Status**: RESOLVED

`_find_source_item_id` used `str(item.get("id") or item.get("node_id") or "")`
which returned `""` for items with no ID, then normalized via `or None` at
call site. The normalization was correct but subtle.

**Fix applied**: `_item_id` helper returns `None` directly when all keys
are falsy. Test `test_empty_string_item_id_collapses_to_none` validates.

---

### F-006-LOW-3 — Static mutation test was brittle (string substring check)

**Severity**: LOW
**Status**: RESOLVED

`test_mutation_performed_is_false_literal` used a string search for
`'"mutation_performed": False'` which would break on formatting changes.

**Fix applied**: Replaced with a behavioral assertion: `plan["mutation_performed"] is False`
plus `type(...) is bool`.

---

## Remaining Risks

- `mypy` not run — type annotations present but not statically checked in CI.
- `compile_action_plan()` does not validate that `blockers` entries are strings —
  a non-string value would propagate silently. Accepted risk; callers are
  expected to pass schema-validated `merge_readiness`.
- `_find_source_item_id` returns the first matching item only. If multiple
  items share a blocker, only one source ID is recorded. Accepted behavior
  for v1 (action plan is aggregated at blocker level, not item level).

---

## Validation

| Check | Result |
|---|---|
| pytest tests/pr_action_bridge/ (52 tests) | PASS |
| pytest tests/audit/ (84 prior tests) | PASS |
| Action ID sequential invariant | PASS |
| compile_action_plan renamed (no builtin shadow) | PASS |
| Input validation for required keys | PASS |
| Unknown blocker silently skipped (tested) | PASS |
| Empty string item ID → None (tested) | PASS |
| schema if/then READY→empty actions | PASS |
| mutation_performed const false (schema + runtime) | PASS |
| No tools.pr_merge import | PASS |
| No gh mutation calls in compiler | PASS |
| No trailing whitespace in docs | PASS |
| mypy | NOT_RUN |
