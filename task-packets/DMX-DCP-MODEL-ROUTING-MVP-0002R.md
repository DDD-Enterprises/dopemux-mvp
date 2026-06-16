---
id: DMX-DCP-MODEL-ROUTING-MVP-0002R
title: Routing Classifier Reconciliation
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Reconciliation packet locking five already-implemented DCP routing
  classifier invariants with new unit tests; six lane-concept cases deferred to
  the 0003+ lane engine.
---

# DMX-DCP-MODEL-ROUTING-MVP-0002R — Routing Classifier Reconciliation

**Series**: DMX-DCP-MODEL-ROUTING-MVP
**Packet**: 0002R (Reconciliation)
**Type**: Test-authoring + packet documentation
**Status**: COMPLETE
**Branch**: `feat/dcp-routing-0002R-reconciliation`
**Author**: Subagent (worktree agent-ac40085c9f974d0cd)
**Date**: 2026-06-16

---

## Objective

Lock down the behavioural invariants of the already-implemented routing classifier
(`src/dopemux/dcp/routing_classifier.py`) by authoring 5 new unit tests that assert
existing, observed behaviour — no new classifier fields or logic were introduced.

The scope was deliberately narrowed from the original 12-case gate packet to 5 cases,
per supervisor decision: the 6 lane-concept cases require fields that do not yet exist in
the pure-flag classifier and are explicitly deferred to a later lane-engine packet.

---

## Files Touched

| File | Operation | Lines changed |
|------|-----------|---------------|
| `tests/unit/dcp/test_routing_classifier.py` | Appended 5 new test functions | +117 lines |
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0002R.md` | Created (this file) | new |

Files NOT touched (read-only inspection only):

- `src/dopemux/dcp/routing_classifier.py`
- `src/dopemux/dcp/routing_model.py`

---

## Tests Added

All 5 tests assert ALREADY-IMPLEMENTED behaviour. Running them without any source
change must produce 5 new PASSes.

### 1. `test_unknown_authority_blocks_mutation`

**Covered invariant**: When `has_unknown_authority=True` and
`authority_class=AuthorityClass.UNKNOWN`, the classifier must not be runnable
AND must not include any mutation-capable action (`edit_allowlisted_files`,
`open_pr`, `run_embedded_audit`) in `allowed_actions`.

**Source path**: `_derive_route_status` → `RouteStatus.UNKNOWN` for unknown
authority; `_derive_allowed_actions` → `_READ_ONLY_BASE_ALLOWED` for non-ALLOWED
status; `is_runnable()` → False (status != ALLOWED).

---

### 2. `test_dopetask_boundary_blocks_dcp_core_execution`

**Covered invariant**: When `requires_dopetask_execution=True` the decision must
not be runnable AND `forbidden_actions` must contain at least one token with
"dopetask" (both `"execute_dopetask"` from `_ALWAYS_FORBIDDEN` and
`"execute_dopetask_live"` from the conditional path).

**DCP-core-execution boundary**: Dopetask execution is never delegatable through
the pure-flag classifier. This test pins the boundary explicitly so it cannot
silently regress.

---

### 3. `test_live_write_without_contract_blocks`

**Covered invariant**: `requires_live_write=True` alone must produce
`status=RouteStatus.BLOCKED` and `is_runnable()=False`. No contract, proof path,
or authority override in the current pure-flag classifier can open a live-write
route — the RED_LANE gate is unconditional.

**Source path**: `_derive_red_lane_state` → `RedLaneState.RED_LANE` when
`requires_live_write` is set; `_derive_route_status` → `RouteStatus.BLOCKED` for
RED_LANE.

---

### 4. `test_unresolved_review_threads_block_readiness`

**Covered invariant**: `has_stale_proof=True` produces `status=RouteStatus.BLOCKED`
and `is_runnable()=False`.

**Docstring note** (pinned in the test): "Unresolved review threads" as a PR-Steward
readiness concern is a HIGHER-LAYER check that lives outside this classifier. The
`has_stale_proof` gate is the analogous in-classifier gate: a route with stale or
invalidated evidence is not actionable until proof is refreshed.

**Source path**: `_derive_route_status` line ~217 — `if inp.has_stale_proof: return
RouteStatus.BLOCKED`.

---

### 5. `test_secret_pattern_routes_to_supervisor`

**Covered invariant**: `touches_secrets=True` must simultaneously satisfy:
1. `is_red_lane()` returns `True` (RED_LANE state).
2. `audit_requirement is AuditRequirement.SUPERVISOR_AUDIT`.
3. `escalation_requirement is EscalationRequirement.ALWAYS`.

Three invariants are locked together because they derive from the same flag and
must move in lockstep. A regression in any one of the three is a security issue.

**Source path**: `_derive_red_lane_state` (touches_secrets → RED_LANE),
`_derive_audit_requirement` (touches_secrets → SUPERVISOR_AUDIT),
`_derive_escalation_requirement` (touches_secrets → ALWAYS).

---

## DEFERRED Cases

The following 6 lane-concept cases from the original gate-packet scope are
**explicitly deferred** to 0003+ lane-engine work.

**Rationale**: The pure-flag classifier contains no bridge/proxy lane fields,
no retrieval-derived lane fields, no secure-MCP-readonly lane fields, no
ECC-intake lane fields, and no opencode/grok wrapper-proof lane fields.
These concepts are architecturally labelled `ACCEPTED_LATER` in the DCP
architecture; introducing them here would require adding new classifier fields
and policy branches — scope that belongs in a dedicated lane-engine packet.

| # | Lane concept | Why deferred |
|---|-------------|--------------|
| 2 | Bridge / proxy lane | No bridge/proxy fields in current classifier |
| 3 | Retrieval-derived lane | No retrieval-source or retrieval-confidence fields |
| 6 | Secure-MCP-readonly lane | `requires_mcp_call` → RED_LANE by current policy; secure-readonly MCP is a future ACL layer |
| 7 | ECC-intake lane | No ECC-source or ECC-validation fields |
| 11 | OpenCode wrapper proof | No opencode-wrapper or proof-envelope fields |
| 12 | Grok wrapper proof | No grok-wrapper or proof-envelope fields |

These are not regressions. They are ACCEPTED_LATER scope items that belong to the
0003+ lane engine design work.

---

## Validation Results

```
PYTHONPATH=src python -m compileall -q src/dopemux/dcp
# exit 0 — no compile errors

PYTHONPATH=src python -m pytest -v tests/unit/dcp/ tests/dcp/test_dcp_model_routing_0001_domain.py
# baseline: 186 passed  (before this packet)
# after:    191 passed  (+5 new tests)
# exit 0
```

---

## Scope Confirmation

- Zero new fields added to `RoutingClassificationInput`.
- Zero new methods added to `RouteDecision`.
- Zero edits to any `src/dopemux/dcp/*.py` file.
- Zero edits to `.github/workflows/`, `services/`, or any other file outside the allowlist.
- Two and only two files modified/created: `tests/unit/dcp/test_routing_classifier.py`
  and this packet document.

---

## Rollback

```bash
git revert HEAD   # reverts both changes in one commit
# or
git checkout main -- tests/unit/dcp/test_routing_classifier.py
git rm task-packets/DMX-DCP-MODEL-ROUTING-MVP-0002R.md
```
