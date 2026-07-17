---
id: TP-DCP-MCP-RO-0018
title: Exact-Head Proof Readiness Evaluator
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Fail-closed exact-head readiness evaluation for the DCP multi-provider series final governance packet.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0018

## Objective

Bind proof/readiness evaluation to an exact head SHA and fail closed on stale
proof, skipped audit, bad/pending checks, unknown reviewers, unresolved
threads, and allowlist escapes — without changing branch protection or
embedded-audit routing.

## Scope

IN: evaluator library + CLI, negative unit tests, docs, packet/proof.

OUT: branch protection edits, auto-merge, secrets, auditor route changes,
claiming series production READY without trusted audit + full live acceptance.

## Validation

```text
uv run --frozen pytest -q tests/audit/test_exact_head_readiness.py
uv run --frozen python scripts/audit/exact_head_readiness.py --help
```

## Rollback

Revert TP-0018 commits. Existing PR Steward artifacts remain independently usable.
