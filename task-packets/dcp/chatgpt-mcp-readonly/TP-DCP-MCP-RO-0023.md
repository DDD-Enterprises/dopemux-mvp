---
id: TP-DCP-MCP-RO-0023
title: Live-Local Acceptance Pass
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-17'
last_review: '2026-07-17'
next_review: '2026-10-15'
prelude: Execute every locally-runnable live acceptance gate against the Gate-0C exemplar with receipts.
---

# TP-DCP-MCP-RO-0023 - Live-Local Acceptance Pass

Objective: Execute the live-local acceptance pass: run the opt-in live facade suite (DCP_FACADE_LIVE_TESTS=1) and the acceptance-harness 'Deterministic + live' gates against the verified Gate-0C exemplar set, exercising real ownership verification (Tier A evidence), live protocol fingerprints, safe-adapter reads against live ConPort/dope-memory, resolution receipts, and the local negative battery (dead container, stale runtime row, foreign process on expected port, invalid lease on reserved port, ambiguous duplicate runtime, cross-repo mount) - producing live proof current to the exact head.

Depends on: TP-DCP-MCP-RO-0020, TP-DCP-MCP-RO-0022. Executor: shell.

See the JSON load packet for invariants, validation commands, and step detail.
