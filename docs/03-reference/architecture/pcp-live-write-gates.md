---
id: PCP-LIVE-WRITE-GATES
title: PCP Live-Write Readiness Gate Contract
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: PCP Live-Write Readiness Gate Contract (reference) for dopemux documentation
  and developer workflows.
---
# PCP Live-Write Readiness Gate Contract

## 1. Purpose and Scope

This document defines the **LIVE_WRITE_READY** contract — the fail-closed gate that every
future live write against any surface governed by the Project Control Plane (PCP) must pass
before execution.

**CONTRACTS-ONLY**: No live write is performed by this document or by Packet 10
(`TP-DMX-PCP-LIVE-WRITE-GATES-0001`). The gate is a schema-level readiness declaration only.

The gate is enforced at the schema level via
`schemas/project_control_plane/live_write_ready.schema.json` (JSON Schema Draft 2020-12).

---

## 2. The Fail-Closed Rule

**No live write is permitted anywhere until every precondition exists and passes.**

READY is withheld on ANY missing, null, false, or non-passing precondition. There is no
partial READY. A READY assertion with one weak precondition is schema-invalid.

The schema's `allOf` gates enforce this at validation time:

- If `status` is `"READY"`, ALL preconditions must be present and passing and
  `blocked_reasons` must be empty (`maxItems: 0`).
- If `status` is `"BLOCKED"` or `"NEEDS_SUPERVISOR"`, `blocked_reasons` must contain at
  least one entry (`minItems: 1`).

---

## 3. Preconditions

Every precondition below must be satisfied before a LIVE_WRITE_READY assertion may carry
`status: "READY"`.

| Precondition | Schema field | READY requirement | Blocked reason when missing/false |
|---|---|---|---|
| Canonical writer | `canonical_writer` | Non-null, non-empty string | `MISSING_CANONICAL_WRITER` |
| Diff within allowlist | `allowlist.diff_within_allowlist` | `true` | `DIFF_OUTSIDE_ALLOWLIST` |
| Approval granted | `approval.approved` | `true` | `MISSING_APPROVAL` |
| Idempotency confirmed | `idempotency.idempotent` | `true` | `NOT_IDEMPOTENT` |
| Rollback available | `rollback.available` | `true` | `NO_ROLLBACK` |
| Dry-run performed | `dry_run_proof.performed` | `true` | `MISSING_DRY_RUN_PROOF` |
| Audit performed | `independent_audit.performed` | `true` | `MISSING_INDEPENDENT_AUDIT` |
| Audit is independent | `independent_audit.independent` | `true` | `AUDIT_NOT_INDEPENDENT` |
| Audit passed | `independent_audit.status` | `"PASS"` | `AUDIT_NOT_PASSED` |
| Post-write verification planned | `post_write_verification.planned` | `true` | `MISSING_POST_WRITE_VERIFICATION` |

### 3.1 Canonical Writer

The canonical writer is the only surface authorized to perform the write. A `null` value
means the writer is unknown and READY is withheld. The canonical writer is identified via
the PCP authority map (`schemas/project_control_plane/authority_map.schema.json`).

### 3.2 Allowlist

The allowlist declares the set of paths the write operation is permitted to touch. If any
file the write will touch falls outside the declared paths, `diff_within_allowlist` is
`false` and READY is withheld. For a READY assertion, `allowlist.paths` must contain at
least one entry — an empty paths array makes `diff_within_allowlist: true` vacuously true
and is schema-invalid under READY status.

### 3.3 Approval

Approval must be granted by a known, authorized human or operator. The `approver` field
records identity; `approval_ref` records the approval artifact (e.g. PR comment URL,
ConPort decision ID).

### 3.4 Idempotency

The write operation must be safe to replay without producing additional side effects.
An idempotency `key` should be recorded so that duplicate executions can be detected
and suppressed.

### 3.5 Rollback

A concrete rollback path must be identified before the write executes. The `plan` field
must name specific commands or steps sufficient to undo the write. For a READY assertion,
`plan` must be a non-empty string — `null` and empty string are both schema-invalid under
READY status.

### 3.6 Dry-Run Proof

A dry-run of the write must be performed and its output inspected before the live write
is authorized. The `proof_ref` field records the dry-run output artifact.

### 3.7 Independent Audit (AIR Red Line #9)

The write must be audited by a party independent of the implementer. The implementer is
never the sole final auditor. The audit must:

- be `performed: true`
- be `independent: true` (auditor identity differs from implementer)
- have `status: "PASS"` (FAIL or NOT_RUN both withhold READY)

### 3.8 Post-Write Verification

A post-write verification plan must exist before the write executes (`planned: true`).
The `performed` field tracks whether verification has run (expected `false` at gate-assertion
time; updated after the write completes).

---

## 4. Schema Enforcement

The schema enforces the fail-closed contract at the structural level via two `allOf` gates:

**Gate A — READY requires all preconditions:**

```
if status == "READY" then:
  canonical_writer: non-null, non-empty string
  allowlist.diff_within_allowlist: true
  allowlist.paths: non-empty array (minItems: 1)
  approval.approved: true
  idempotency.idempotent: true
  rollback.available: true
  rollback.plan: non-empty string (minLength: 1)
  dry_run_proof.performed: true
  independent_audit.performed: true
  independent_audit.independent: true
  independent_audit.status: "PASS"
  post_write_verification.planned: true
  blocked_reasons: [] (maxItems: 0)
```

**Gate B — BLOCKED/NEEDS_SUPERVISOR requires a reason:**

```
if status in ["BLOCKED", "NEEDS_SUPERVISOR"] then:
  blocked_reasons: minItems 1
```

**Const sentinel:** `live_write_performed` is pinned `const: false` in the schema. A
`LIVE_WRITE_READY` assertion can never record that a live write was performed — it is a
readiness declaration only.

---

## 5. Forbidden Wiring (Red Line #15)

The following wiring must never be enabled until a passing `LIVE_WRITE_READY` assertion
exists and covers the target operation:

- `scripts/batch_resolve_and_merge.py` — batch PR merge automation
- `src/dopemux_pr_merge_specialist/queue_drain.py` with `execute=True` — queue drain
  execution path

These paths implement live write logic and are gated behind Red Line #15. No code in this
packet (schema, tests, or this document) references or imports either path.

---

## 6. Relationship to Packet 11

This packet (`TP-DMX-PCP-LIVE-WRITE-GATES-0001`, Packet 10) is the prerequisite gate for
Packet 11, which implements the FastAPI bridge live adapter. Packet 11 must not be executed
until a passing `LIVE_WRITE_READY` assertion — validated against this schema — exists for
each write operation the adapter will perform.

The sequencing invariant is:

```
Packet 10 (this packet) → LIVE_WRITE_READY schema + tests + doc (CONTRACTS ONLY)
Packet 11               → FastAPI bridge live adapter (first live-write executor)
```

Packet 11 must reference a `LIVE_WRITE_READY` assertion by `assertion_id` in its proof
bundle and confirm `status: "READY"` before any executor path is enabled.

---

## 7. Validation Commands

Validate the schema itself:

```bash
python -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('schemas/project_control_plane/live_write_ready.schema.json')))"
```

Run the gate tests:

```bash
python -m pytest -q tests/project_control_plane/test_live_write_gates.py
```

Run the full project_control_plane test suite to check for regressions:

```bash
python -m pytest -q tests/project_control_plane/ tests/dcp_extension/ tests/dnh_extension/
```
