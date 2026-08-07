---
id: TP-DOPECONTEXT-TEST-HARNESS-0005
title: Tp Dopecontext Test Harness 0005
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Repair the nine failing MCP tool tests so the dope-context tool surface
  becomes testable end to end, unblocking verification of the blockers.
---
# Task Packet: TP-DOPECONTEXT-TEST-HARNESS-0005

## Objective

Make the dope-context MCP tool surface testable again. Nine tests in
`test_mcp_server.py` fail with `TypeError: 'FunctionTool' object is not
callable` — and they are precisely the tests covering `search_code`,
`index_workspace`, `docs_search`, and `search_all`, the paths that carry the
two blocking findings from the PR #1112 audit.

## Status

`IMPLEMENTATION_CANDIDATE`

Closes **F-008**. Should land before `TP-DOPECONTEXT-VECTOR-SPACE-0004`, whose
verification is otherwise limited to the function level.

## Risk

`LOW`

Test infrastructure only. No runtime behaviour changes. The risk is writing
tests that pass against a mis-shaped stub, which is what the current suite
already does elsewhere.

## The Finding

The nine failures reproduce identically at pre-merge base `603871f96a` and at
merged main `f4e91574a1`, so they are pre-existing and were not caused by
PR #1112. The cause is that FastMCP wraps `@mcp.tool()`-decorated functions in a
`FunctionTool` object which is not directly callable, while the tests invoke the
decorated name as a plain coroutine.

The consequence is what matters: the service's own suite **cannot** detect an
index/query model divergence, because every tool-level test errors before
reaching an assertion. PR #1112 shipped a 2,000-line change into a suite that
structurally could not exercise its central risk.

Two of the nine additionally surface `AttributeError`/`KeyError` from gaps in
the `AsyncQdrantClient` stub, notably a missing `get_collection`.

## Scope

### IN

- invoking the underlying coroutine rather than the `FunctionTool` wrapper, in
  all nine failing tests
- filling the `AsyncQdrantClient` stub gaps those tests hit, at minimum
  `get_collection`
- one shared helper so future tool tests do not repeat the workaround
- a test asserting the code content index model equals the code content query
  model, which is only expressible once the tool surface runs

### OUT

- changing any runtime behaviour in `src/`
- the collection gate, the vector-space decision, or the remainder hardening
- rewriting tests that currently pass
- upgrading or pinning FastMCP

## Invariants

- No file under `services/dope-context/src/` is modified.
- No test is made to pass by weakening its assertion.
- A stub that accepts an argument the real SDK rejects is a defect, not a fix.
- The nine tests must exercise the real tool bodies, not a reimplementation.

## Allowed Files

- `services/dope-context/tests/test_mcp_server.py`
- `services/dope-context/tests/conftest.py`
- `services/dope-context/tests/test_vector_space_invariants.py`
- `task-packets/dope-context/TP-DOPECONTEXT-TEST-HARNESS-0005.md`

## Required Chain

`analyze -> planner -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

## Plan

1. Determine the correct accessor for the wrapped coroutine on the installed
   FastMCP version rather than guessing; record the version and the accessor.
2. Add one shared test helper that resolves a decorated tool to its callable.
3. Apply it to the nine failing tests without altering their assertions.
4. Fill the `AsyncQdrantClient` stub gaps, checking each added method against
   the real client signature so the stub cannot accept impossible arguments.
5. Add the index/query model agreement test now that the tool surface runs.
6. Confirm the suite reaches zero failures, and that no previously passing test
   changed meaning.

## Exact Commands

```bash
git status --short --branch
git diff --check
PYTHONPATH=services/dope-context python -m pytest -q services/dope-context/tests
PYTHONPATH=services/dope-context python -m pytest -q \
  services/dope-context/tests/test_mcp_server.py -v
python -c "import fastmcp; print(fastmcp.__version__)"
git diff --stat
git diff
```

## Acceptance Criteria

- `services/dope-context/tests` reports **zero** failures.
- All nine previously failing tests pass by exercising the real tool bodies.
- No file under `services/dope-context/src/` is modified.
- No previously passing test had an assertion weakened or removed.
- Every stub method added matches the real `AsyncQdrantClient` signature.
- A test asserts code content index model equals code content query model.

## Proof Requirements

Return verbatim: the installed FastMCP version and the accessor used, base and
final head SHA, `git status` before and after, `git diff`, the pytest summary
before and after showing 9 failures going to 0, the full `-v` output for
`test_mcp_server.py`, and confirmation that `git diff --name-only` contains no
path under `src/`.

## Rollback

Revert the packet commits. Tests return to their current state; no runtime
behaviour is affected either way.

## Stop Conditions

Stop if:

- passing a test requires modifying anything under `src/`
- passing a test requires weakening an assertion
- the installed FastMCP version exposes no supported way to reach the coroutine,
  in which case record the finding and stop rather than reimplementing the tool
- a stub method cannot be matched to a real SDK signature
- embedded audit returns FAIL or NEEDS_SUPERVISOR

## Current Evidence

### OBSERVED

- Nine failures, identical at `603871f96a` and `f4e91574a1`.
- All nine are in `test_mcp_server.py`.
- Primary cause `TypeError: 'FunctionTool' object is not callable`.
- Secondary cause `'AsyncQdrantClient' object has no attribute 'get_collection'`.
- Suite totals on merged main: 9 failed, 34 passed, 1 skipped.
- After `TP-DOPECONTEXT-VOYAGE4-REPAIR-0002`: 9 failed, 43 passed, 1 skipped.

### UNKNOWN

- the installed FastMCP version's supported accessor for the wrapped coroutine
- whether any of the nine hide a second defect behind the first error
