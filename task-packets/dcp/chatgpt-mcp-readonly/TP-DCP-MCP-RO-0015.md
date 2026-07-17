---
id: TP-DCP-MCP-RO-0015
title: Ownership Verification And Release-One Adapters
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Fail-closed ownership verification and release-one ConPort/dope-memory adapter gates.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0015

## Objective

Prove ownership of runtime candidates without port-only trust, and expose only
release-one safe adapter operations for ConPort decisions and dope-memory
search/replay behind that verdict.

## Scope

IN: ownership verifier, release-one safe adapter gate, decision-by-id helper,
route manifest release-one tables, tests, docs, packet, proof.

OUT: live network by default, tunnels, writes, progress reads, dope-context,
task-orchestrator, bridge, public tool surface expansion, credentials.

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_ownership.py services/dcp-readonly-facade/tests/test_safe_adapters.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
```

## Rollback

Revert the TP-0015 commits. Legacy Phase-1 helpers remain; release-one gate is
removed.
