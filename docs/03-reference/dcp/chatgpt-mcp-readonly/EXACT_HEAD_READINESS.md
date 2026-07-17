---
id: dcp-mcp-readonly-exact-head-readiness
title: DCP Exact-Head Proof Readiness Evaluator
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Fail-closed exact-head readiness evaluation for DCP multi-provider series proofs without mutating branch protection or audit routing.
---

# Exact-Head Proof Readiness

Packet: **TP-DCP-MCP-RO-0018**

## Purpose

Emit a local `MERGE_READINESS`-style verdict bound to an exact git head.
**READY** only when proof, audit, checks, reviews, and scope all match that head.

This evaluator does **not**:

- change branch protection
- enable auto-merge
- alter `embedded-audit.yml` routing
- claim AGY satisfies trusted embedded audit

## Module / CLI

| Surface | Path |
| --- | --- |
| Library | `src/dopemux/audit/exact_head_readiness.py` |
| CLI | `scripts/audit/exact_head_readiness.py` |

```bash
uv run --frozen python scripts/audit/exact_head_readiness.py \
  --head-sha "$(git rev-parse HEAD)" \
  --proof-json proof/TP-DCP-MCP-RO-0017/PROOF.json \
  --checks-json /path/to/checks.json \
  --out proof/TP-DCP-MCP-RO-0018/MERGE_READINESS.json
echo $?   # 0 only when status==READY
```

## Fail-closed blockers

| Condition | Blocker code |
| --- | --- |
| Proof head ≠ requested head | `proof_stale_to_head` |
| Embedded audit SKIPPED/FAIL/missing | `embedded_audit_*` |
| Failed checks | `failed_checks` |
| Pending checks | `pending_checks` |
| Checks for other SHA | `checks_stale_to_head` |
| Unknown reviewer/bot | `unknown_reviewers_or_bots` |
| Unresolved blocking thread | `blocking_thread_unresolved` |
| Diff outside allowlist | `diff_escapes_packet_allowlist` |
| Acceptance `release_ready` false (when required) | `acceptance_release_not_ready` |

## Relationship to TP-0017

When `--require-acceptance-ready` is set, a TP-0017
`acceptance_report.json` with `release_ready: false` keeps status **BLOCKED**.
Local-live-only acceptance is therefore **not** merge-ready for production
exposure until vendor live gates pass.
