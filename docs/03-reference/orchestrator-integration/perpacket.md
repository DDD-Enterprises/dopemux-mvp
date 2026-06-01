---
id: perpacket
title: Per-Packet Test Isolation and Validation
type: reference
owner: '@hu3mann'
date: '2026-05-28'
related_packets:
- TP-DMX-ORCH-PROOF-PERPACKET-001
author: '@hu3mann'
last_review: '2026-05-28'
next_review: '2026-08-26'
prelude: Per-Packet Test Isolation and Validation (reference) for dopemux documentation
  and developer workflows.
---
# Per-Packet Test Isolation & Validation Reference

This document outlines the workflow and toolchain for validating Task Packets in absolute isolation within the `DMX-ORCH-INTEGRATION-FOLLOWUP` series.

## Overview
To prevent whole-bundle test bloat, each Task Packet declares its own targeted unit tests and verify commands in the declarative test mapping file:
*   [config/orchestrator/perpacket_test_map.yaml](file:///Users/hue/code/dopemux-mvp/config/orchestrator/perpacket_test_map.yaml)

A developer or agent can run isolated validation and code review for a single packet, producing the structured proof snippets required for [AGENTS.md §9 (Proof and Finality)](file:///Users/hue/code/dopemux-mvp/AGENTS.md#9-proof-and-finality).

---

## 🛠️ Commands Reference

### 1. Isolated Validation Command
To execute all targeted tests and JSON-schema checks for a specific Task Packet:
```bash
dopemux orchestrator perpacket validate <PACKET_ID> [--json-output]
```

*   **Standard View**: Prints a human-readable list of each validation name, its status (`PASS` or `FAIL`), and its exit code.
*   **JSON View (`--json-output`)**: Prints only the structured validations JSON snippet. This snippet can be directly pasted into the packet's `PROOF.json` `validations[]` list.

### 2. Differential Code Review Command
To run targeted `pal/codereview` against the Git diff of the packet's allowlist:
```bash
python3 scripts/orchestrator/perpacket_codereview.py <PACKET_ID>
```
*   Invokes the local `pal` MCP server running on port `3003`.
*   Prints the copy-pasteable JSON `codereview_status` snippet.
*   If the `pal` server is offline or unreachable, it cleanly defaults to a `NOT_RUN` placeholder, ensuring zero process interruption.

---

## 🔄 Lifecycle Progression

### Advancing to `PASS`
A Task Packet's validations are considered passing when:
1.  All targeted unit tests execute successfully with exit code `0`.
2.  The Task Packet JSON complies fully with the [dopetask-canonical-spec.json](file:///Users/hue/code/dopemux-mvp/docs/03-reference/spec/dopetask/dopetask-canonical-spec.json).
3.  The final `PROOF.json` passes structural validation.

Once passing, the operator or agent can update the packet's `PROOF.json` status to `READY_FOR_REVIEW`, completing the mechanical **complete-gate** under `AGENTS.md §9`.
