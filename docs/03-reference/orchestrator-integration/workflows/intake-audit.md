---
id: orchestrator-intake-audit
title: Intake & Red-Team Audit Workflow
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference explaining structured intake verification and safety-tier auditing routines.
related_packets:
  - TP-DMX-ORCH-011
---

# Intake & Red-Team Audit Workflow

Provides a formal, structured red-team audit flow on newly ingested task packets before scheduling them in the active execution queue.

## Audit Tiers
*   **T0/T1 (Read-Only)**: Verifies allowlists and branch targets.
*   **T2/T3 (Advisory-Gated)**: Audits race conditions, WAL thread locks, and dependency topological ordering.
*   **T5 (Mutation-Gated)**: Asserts the presence of a typed approval phrase.
