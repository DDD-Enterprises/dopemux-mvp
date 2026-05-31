---
id: orchestrator-memory-index
title: Memory Writers & Mirroring Reference
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference for ConPort decision and progress write operations with dope-memory mirroring.
related_packets:
  - TP-DMX-ORCH-009
  - TP-DMX-ORCH-009-LIVE
---

# ConPort Writers & dope-memory Mirroring

This reference details the live database write operations and mirroring strategies implemented within the `memory_writers` module.

## Canonical Writers & Authority
*   **ConPort** is the sole authority for recording Decisions and progress tracks.
*   **dope-memory** mirrors ConPort writes to build a temporal chronicle.

## Write Receipts
Every write outputs a deterministic JSON receipt capturing:
```json
{
  "canonical_writer": "conport",
  "requested_by": "gemini-mcp",
  "approval_id": "TU-009-APPR",
  "mirror_status": "PASSED"
}
```
If the dope-memory mirror write fails, ConPort state is left intact, reporting `PARTIAL` success with `mirror_status: FAILED`.
