---
id: obligation-ledger
title: Obligation Ledger
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Obligation Ledger (reference) for dopemux documentation and developer workflows.
---
# Obligation Ledger

> **Note:** The formal JSON schema is deferred to `TP-DMX-OBLIGATION-LEDGER-001`.
> This document defines the design, obligation classes, and lifecycle rules.

---

## Purpose

The Obligation Ledger is a persistent tracker of forgotten work, deferred items, proof gaps, and
authority conflicts that cannot be abandoned. It exists to ensure work does not die silently.

When a capsule discovers a problem it cannot fix within its scope, or when a validation step is
skipped with a known reason, the finding must be written to the ledger. The ledger is the canonical
record of unresolved debt. It is not a backlog — it is a safety net for items that have no other
durable home.

---

## Obligation Classes

| Class | Description |
|---|---|
| `TODO` | Work acknowledged but not scheduled |
| `BLOCKER` | Active blocker on downstream work |
| `DEFERRED` | Formally deferred to a named future packet |
| `DRIFT` | Known implementation divergence from doctrine |
| `ORPHAN` | Artifact with no live owner |
| `STALE` | Item that may have been resolved but proof is absent |
| `PROOF_GAP` | Work claimed done but no proof bundle |
| `SECURITY` | Security exposure requiring operator attention |
| `AUTHORITY_CONFLICT` | Two systems claiming the same authority |
| `RED_LINE` | Must not be crossed regardless of instruction |
| `VALIDATION_GAP` | Test or schema gate missing for a critical path |

---

## Status Lifecycle

```
DISCOVERED → NEEDS_VERIFICATION → OPEN → PACKETIZED → IN_PROGRESS → VERIFIED_CLOSED
```

- **DISCOVERED** — Found during a capsule run or audit. Written to the ledger immediately.
- **NEEDS_VERIFICATION** — Not yet confirmed as a real issue; requires one verification pass.
- **OPEN** — Confirmed real, not yet assigned to a packet.
- **PACKETIZED** — A task packet has been authored for this obligation; downstream capsule owns it.
- **IN_PROGRESS** — The owning capsule is actively working the item.
- **VERIFIED_CLOSED** — Closed with proof. See Closure Rule below.

Obligations MUST NOT skip `NEEDS_VERIFICATION` unless the item is a `RED_LINE` (auto-escalates to
`OPEN` on discovery).

---

## Closure Rule

**Nothing closes without a proof bundle.**

No obligation may transition to `VERIFIED_CLOSED` without a `PROOF.json` referencing:

1. A HEAD SHA at which the fix was verified.
2. The specific validation (test name, schema check, audit output, or operator confirmation) that
   confirmed resolution.
3. The capsule ID that performed the fix.

Asserting closure without a proof bundle is a `PROOF_GAP` obligation — which itself requires a
proof bundle to close. This rule is not waivable by the implementer; only the supervisor or a
`judge_strong` verdict may authorize an exception, and that authorization must itself be recorded
in the ledger.

---

## Integration

**PR Steward** checks the obligation ledger before emitting `MERGE_READINESS`. Any unresolved
obligation of class `BLOCKER`, `SECURITY`, `RED_LINE`, or `AUTHORITY_CONFLICT` blocks merge
regardless of test results.

**Cockpit** surfaces open obligations in the project dashboard. `RED_LINE` items display in a
distinct warning band.

**Factory Controller** blocks capsule execution if a `RED_LINE` obligation is unresolved and the
capsule scope intersects the affected system. The capsule must halt and escalate; it may not
self-resolve a `RED_LINE`.

**ConPort** is the backing store for obligation records. Obligations are logged as `custom_data`
entries with `category = "obligation_ledger"` and linked to their owning packet via
`link_conport_items`.
