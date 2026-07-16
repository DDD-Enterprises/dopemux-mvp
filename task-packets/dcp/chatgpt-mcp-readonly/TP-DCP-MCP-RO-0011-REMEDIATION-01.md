---
id: TP-DCP-MCP-RO-0011-REMEDIATION-01
title: Runtime Catalog Join Generated Identity Remediation
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Narrow correction to the open TP-DCP-MCP-RO-0011 PR. The remediation aligns
  pure runtime evidence matching with lifecycle-generated project identity without
  changing DCP target authorization or adding live behavior.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0011-REMEDIATION-01

## Objective

Repair the post-merge TP-DCP-MCP-RO-0011 runtime/catalog join in PR #1055 so
lifecycle-generated runtime records with matching project and worktree roots
become an internal non-callable candidate. The registry `.repo_id` identity
remains the earlier DCP target-authorization check and is not used as the
lifecycle record ID.

## Scope

IN:

- Pure `ProjectIdentity`-based runtime ID calculation in the join.
- Lifecycle-shaped focused regression coverage.
- Contract, build-series, remediation-packet, and remediation-proof records.

OUT:

- Any lifecycle, catalog, resolver, server, adapter, backend, container,
  tunnel, provider, credential, listener, or caller-contract change.
- Changes to the executed TP-DCP-MCP-RO-0011 packet or proof directory.

## Invariants

- The join is pure, dependency-injected, advisory, redacted, and
  `callable=false`.
- Generated runtime project identity is derived through the shared
  `ProjectIdentity` value model, not a local duplicate algorithm.
- DCP target authorization still validates `.repo_id` before joining runtime
  evidence.
- Missing, malformed, wrong-root, wrong-ID, and ambiguous records remain
  fail-closed.
- The pre-existing generated `.claude/claude_config.json` delta is outside the
  allowlist and will not be staged.

## Plan

1. Confirm the historical #1041 merge, replacement PR #1055 head, and trace
   `.repo_id`, `ProjectIdentity`, lifecycle, runtime-registry, and join
   identities.
2. Add a test whose runtime `project_id` is derived from `ProjectIdentity` and
   verify it fails under the existing comparison.
3. Change only the join to calculate the expected runtime identity from the
   already-resolved roots, then rerun focused tests.
4. Add the inverse wrong-ID assertion, preserve all existing fail-closed cases,
   and run the full facade suite.
5. Document the identity-domain boundary and record validation evidence in a
   new remediation proof directory.
6. Validate the packet, inspect the full allowlisted diff, run precommit, then
   refresh live PR state before any push or PR action.

## Files To Touch

- `services/dcp-readonly-facade/src/dcp_facade/runtime_catalog_join.py`
- `services/dcp-readonly-facade/tests/test_runtime_catalog_join.py`
- `docs/03-reference/dcp/chatgpt-mcp-readonly/RUNTIME_CATALOG_JOIN_CONTRACT.md`
- `docs/03-reference/dcp/chatgpt-mcp-readonly/BUILD_SERIES.md`
- `task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0011-REMEDIATION-01.json`
- `task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0011-REMEDIATION-01.md`
- `proof/TP-DCP-MCP-RO-0011-REMEDIATION-01/**`

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_runtime_catalog_join.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
uv run --frozen python -m compileall -q services/dcp-readonly-facade/src
uv run --frozen python -m jsonschema -i task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0011-REMEDIATION-01.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
git diff --check
```

## Stop Conditions

- The shared project-identity semantics cannot be used without introducing I/O
  into the join.
- The repair requires an edit outside the listed allowlist.
- A lifecycle-shaped test does not reproduce the identity mismatch.
- Any test demonstrates a candidate becoming callable or exposes operational
  topology.
- The PR head changes before final evidence is captured.

## Rollback

Revert only the remediation commit after it is created. The original TP-0011
implementation and its immutable historical proof remain available as the
pre-remediation state.
