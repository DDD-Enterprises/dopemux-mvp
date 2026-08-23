---
id: dcp-mcp-readonly-acceptance-matrix
title: DCP Multi-Provider Acceptance Matrix
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Blocking acceptance matrix for the DCP multi-provider read-only facade series; skipped live gates are never passes.
---

# Acceptance Matrix

Packet: **TP-DCP-MCP-RO-0017**
Rule: every `BLOCKING` row applicable to the release slice must **PASS**.
A skipped live gate is **NOT** a pass.

| Test ID | Risk | Type | Expected (summary) | Blocking |
| --- | --- | --- | --- | --- |
| DCP-ACC-001 | High | Deterministic | Unknown opaque target blocked; no path/existence leak | BLOCKING |
| DCP-ACC-002 | High | Deterministic | Disabled target blocked before workspace inspect | BLOCKING |
| DCP-ACC-003 | Critical | Deterministic | Path outside approved roots blocked | BLOCKING |
| DCP-ACC-004 | High | Deterministic | Missing `.dopemux` blocked; no auto-init | BLOCKING |
| DCP-ACC-005 | Critical | Deterministic | `.repo_id` project mismatch blocked | BLOCKING |
| DCP-ACC-006 | Critical | Live | Wrong-project runtime candidate blocked despite healthy port | BLOCKING |
| DCP-ACC-007 | High | Deterministic + live | Linked worktree roots derive exactly | BLOCKING |
| DCP-ACC-008 | Critical | Live | Stale runtime rejected; no port-only accept | BLOCKING |
| DCP-ACC-009 | Critical | Live | Other-project healthy service blocked before adapter | BLOCKING |
| DCP-ACC-010 | Critical | Deterministic + live | Ambiguous candidates block | BLOCKING |
| DCP-ACC-011 | Critical | Deterministic | Missing family policy blocks capability | BLOCKING |
| DCP-ACC-012 | High | Deterministic | Blocked family tools absent/denied before live probe | BLOCKING |
| DCP-ACC-013 | Critical | Deterministic + live | Connector target authz matrix (A/B/invented) | BLOCKING |
| DCP-ACC-014 | Critical | Deterministic | Denied tools blocked before adapter | BLOCKING |
| DCP-ACC-015 | Critical | Deterministic + provider | Tool manifest has no mutation-shaped tools | BLOCKING |
| DCP-ACC-016 | Critical | Deterministic + live | Progress/side-effect reads denied; state unchanged | BLOCKING |
| DCP-ACC-017 | Critical | Deterministic | Prompt-injection cannot change policy | BLOCKING |
| DCP-ACC-018 | Critical | Deterministic | Path traversal corpus blocked | BLOCKING |
| DCP-ACC-019 | Critical | Deterministic + fs | Symlink escape blocked | BLOCKING |
| DCP-ACC-020 | Critical | Deterministic + live | Synthetic secrets never appear in outputs/logs | BLOCKING |
| DCP-ACC-021 | Critical | Deterministic + live | Authorization header never logged raw | BLOCKING |
| DCP-ACC-022 | High | Deterministic | Rate/concurrency limits fail closed | BLOCKING |
| DCP-ACC-023 | High | Live | Provider discovery matches accepted subset | BLOCKING for enabled provider |
| DCP-ACC-024 | High | Live | ChatGPT tunnel stop fails closed | BLOCKING for ChatGPT |
| DCP-ACC-025 | High | Live | Grok stable hostname survives restart | BLOCKING for Grok |
| DCP-ACC-026 | High | Live | Unsupported transport/model fails closed | BLOCKING |
| DCP-ACC-027 | Critical | Live | Credential revoke/rotate fails old token | BLOCKING |
| DCP-ACC-028 | Critical | Live | Full disable sequence stops external access | BLOCKING |
| DCP-ACC-029 | Critical | Live | Two-worktree isolation | BLOCKING |

## Gate classification

- **Deterministic:** hermetic unit/integration tests; fake transports allowed when they prove no adapter call.
- **Live:** real processes, synthetic data, independently revocable credentials. Requires
  `DCP_ACCEPTANCE_LIVE=1` **and** operator-approved credential/tunnel env (see harness).

## Proof rule

A provider smoke test alone is not trust. Trust requires connector auth, target authz,
live ownership, release-one adapter, redaction, negatives, and exact-head proof.
