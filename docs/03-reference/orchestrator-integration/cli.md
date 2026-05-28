---
id: orchestrator-cli
title: Task Orchestrator CLI Commands
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference for read-only Task Orchestrator subcommands and validation helpers.
related_packets:
  - TP-DMX-ORCH-002
---

# Task Orchestrator CLI Reference

The `dopemux orchestrator` command group exposes several read-only subcommands for status, policy, and validation.

## Active Command Groups

### 1. `dopemux orchestrator packet validate`
Validates a JSON task packet against the canonical `dopetask-canonical-spec.json` schema:
```bash
dopemux orchestrator packet validate <path_to_packet.json>
```

### 2. `dopemux orchestrator proof validate`
Validates the structural compliance of a proof bundle `PROOF.json`:
```bash
dopemux orchestrator proof validate <path_to_proof.json>
```

### 3. `dopemux orchestrator perpacket validate`
Runs targeted Pytest runs and JSON validations mapped to a single Task Packet ID:
```bash
dopemux orchestrator perpacket validate <PACKET_ID>
```
