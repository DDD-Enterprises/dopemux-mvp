---
id: dcp-context-economy-v1
title: "DCP Context Economy V1"
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Preserve mandatory evidence while deterministically limiting optional derived context.
---

# DCP Context Economy V1

Context economy reduces optional context, never mandatory evidence.

## Deterministic order

1. Reserve budget for mandatory runtime/source and accepted-authority evidence.
2. Dereference and verify mandatory evidence.
3. Reject READY when mandatory evidence cannot fit without truncation.
4. Add optional derived evidence only from remaining budget.
5. Preserve stable source order and explicit digests.

`mandatory_evidence_truncation_allowed` is always false in P0. A size limit does
not permit silent omission, summarization, or substitution of required evidence.
Missing budget is a visible blocker.

Derived Wiki pages and retrieval hits may save discovery cost, but they remain
non-canonical and cannot replace their source snapshots.
