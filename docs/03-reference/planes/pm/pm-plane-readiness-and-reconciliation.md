---
id: pm-plane-readiness-and-reconciliation
title: PM Plane Readiness and Reconciliation
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
status: active
prelude: Explains the readiness contracts and reconciliation semantics of PM-plane operations.
---
# PM Plane Readiness and Reconciliation

## Semantics

The Dopemux PM plane leverages a canonical source-of-truth model for workflows, context, and entities. This results in explicit states for writes:
- **Canonical Success**: The authority backend successfully received and persisted the state change.
- **Mirror Failure / Degraded**: An associated mirror system failed to process the update.
- **Pending Reconciliation**: When canonical success occurs but mirror failure happens, the data is safe, but the system state is degraded and needs manual or automated reconciliation.

Metrics and readiness endpoints strictly align with this model:
- `ok` / `healthy` means the canonical systems and all known dependencies are operating properly.
- `degraded` means a system is functioning but there are downstream or dependency failures.
- `fail` means the canonical backend cannot fulfill its contract.

## Runbooks

When dealing with a degraded PM-plane operation, pending reconciliation queues growing, or rogue runtime environments:
Please refer to the actionable runbook: [PM-Plane Runtime Recovery](../../02-how-to/operations/pm-plane-runtime-recovery.md)
