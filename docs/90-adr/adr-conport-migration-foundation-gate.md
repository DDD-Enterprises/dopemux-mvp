---
id: adr-conport-migration-foundation-gate
title: "ADR: ConPort migration foundation gate"
type: adr
owner: '@hu3mann'
author: '@claude'
date: '2026-06-19'
last_review: '2026-06-19'
next_review: '2026-09-17'
prelude: Records the decision to gate enhanced ConPort schema behind an explicit, operator-run, fail-closed migration gate, and the restore + ledger-compatibility hardening applied after the gate was clobbered off main.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-201-conport-kg-security-hardening
---

# ADR: ConPort migration foundation gate

**Status:** Accepted
**Date:** 2026-06-19
**Decision Type:** Architecture / Migration Safety / Contract-Sensitive Startup DDL
**Scope:** ConPort MCP server, `docker/mcp-servers-source/conport/`, DMX-CONPORT-OPTIMAL task packets

## Context

DMX-CONPORT-OPTIMAL contains downstream packets that depend on enhanced ConPort
schema objects (`decision_relationships`, `review_reminders`, `adhd_metrics`,
multi-tenancy tables, unified-query indexes, worktree/instance columns). The
runtime startup path did not prove those objects are applied:

- ConPort startup called `_ensure_schema()`, which checked only for
  `public.workspace_contexts` before returning, then applied `/app/schema.sql`.
- The Dockerfile copied `schema.sql` but **not** the migrations directory.
- Startup also performed hidden `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
  mutations (e.g. `instance_id`, `created_by_instance`) outside any audited
  migration ledger — un-gated DDL on every boot.

This created a hidden prerequisite for downstream packets and weakened
replayability and auditability.

## Decision

Introduce an explicit, **operator-gated, fail-closed** migration gate
(`docker/mcp-servers-source/conport/migrations/conport_migration_gate.py`),
landed by PR #917 (DMX-CONPORT-OPTIMAL-100). The gate:

- discovers the required migration files deterministically and fails closed on
  any missing file;
- refuses to mutate the database unless invoked with both the `apply` subcommand
  and `DPMX_CONPORT_MIGRATION_APPLY=1`;
- maintains an append-style migration ledger
  (`public.conport_schema_migrations`) with per-file checksum + success state;
- verifies ledger rows **and** concrete schema objects (tables, columns,
  indexes, views) on both `apply` and read-only `verify`;
- keeps database passwords out of `psql` process arguments.

Startup no longer performs hidden enhanced-schema `ALTER`s; `enhanced_server.py`
instead logs that enhanced migrations are operator-gated and points at the gate.
The Dockerfile now copies the migrations directory into the image so the gate is
runnable in-container.

## Non-decision

This ADR does **not** authorize silent migration auto-apply on normal ConPort
startup. Any runtime migration runner must remain explicit, operator-gated,
auditable, and fail closed on drift.

## Regression and restore (2026-06-19)

PR #917 merged the gate to `main` (`c45b2c8e7`, 19:58Z). PR #932
("🎨 Palette: Team Dashboard …", `559d7e2fa`, 20:12Z) was based on pre-#917
`main` and its merge **reverted #917 wholesale** — removing the gate and its
tests and restoring `enhanced_server.py`/`schema.sql` to their pre-#917 state
(re-enabling the hidden startup `ALTER`s). No Palette-specific content touched
those ConPort files; this was a stale-branch clobber, not an intentional change.

This ADR's PR restores #917's gate at its canonical path and re-removes the
hidden startup DDL, returning `main` to the operator-gated design.

## Ledger-compatibility hardening (ported from PR #928)

PR #928 (an independent twin implementation of the gate) carried two fail-closed
properties the #917 gate lacked. Those properties — not #928's separate gate
file — are ported into the canonical gate:

1. **Incompatible-ledger fail-closed.** Before reading the ledger on `verify`,
   the gate introspects the ledger table's columns. If the table exists but its
   columns are not a superset of the native schema
   (`{version, filename, checksum_sha256, success}`), or if ledger inspection
   raises an unexpected database error, the gate raises a structured
   `migration ledger validation failed` result instead of leaking an uncaught
   column-level SQL traceback.
2. **No-mutate guard.** On `apply`, if a ledger table already exists whose
   schema this gate does not own, the gate refuses to mutate it
   (`legacy migration ledger cannot be mutated by this gate`) rather than
   blindly writing rows into a foreign ledger.

**Output-contract note:** the #917 gate's established envelope
(`{"status": "pass" | "fail-closed", ...}`, exit `0`/`2`) is preserved. #928's
`applied_verified` / `verified` / `failed` status strings and exit `1` were
**not** adopted, to avoid breaking the merged #917 contract and its test suite.
The hardening's error *messages* are ported verbatim; the *envelope* stays
PR #917's. The word "legacy" in the no-mutate message is PR #928's wording for "a
pre-existing ledger this gate does not own."

## Consequences

- Enhanced ConPort schema is applied only through an explicit, audited,
  operator-run gate; schema-dependent packets cite gate proof before execution.
- ConPort startup is deterministic and free of hidden DDL.
- A foreign or corrupt migration ledger fails closed with a structured error and
  is never silently mutated.
- The gate's native ledger schema and the guard's `NATIVE_LEDGER_COLUMNS`
  constant must stay in sync (enforced by a unit test).

## Accepted amendment: CRS v2 migration boundary

Accepted on 2026-07-21 by the [Wave 1 acceptance record](../../proof/conport-crs-v2/wave1/WAVE1-ACCEPTANCE.json). The migration gate additionally requires:

1. a target-specific schema/migration bundle digest and target epoch;
2. a verified encrypted backup and isolated restore receipt before source mutation;
3. deterministic legacy export and source digest;
4. row-level classification into canonical-safe, alias-resolvable, instance-scoped, packet-scoped, foreign-project, system, test/fixture, or ambiguous;
5. quarantine of ambiguous, foreign, system, and test records unless separately authorized;
6. evidence-based provenance backfill only, with unknown values retained as unknown or quarantined;
7. RLS, idempotency, revision, outbox, and cross-scope negative tests;
8. no hidden DDL and no automatic production migration;
9. no mutation of the legacy migration ledger to imply target acceptance;
10. rollback to a verified accepted epoch before irreversible cleanup.
