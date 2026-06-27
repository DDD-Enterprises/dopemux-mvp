---
id: PCP-ACTIVATION-READINESS
title: PCP/DCP Activation Readiness (Fail-Closed)
type: reference
owner: '@hu3mann'
date: '2026-06-23'
author: '@hu3mann'
last_review: '2026-06-26'
next_review: '2026-09-24'
prelude: PCP/DCP Activation Readiness (Fail-Closed) (explanation) for dopemux documentation
  and developer workflows.
---
# PCP/DCP Activation Readiness

This runbook describes **activation preconditions only**. It does **not** claim production activation is complete.

## Bridge inertness

- The FastAPI bridge is **inert by default**.
- **No default writer** exists.
- Top-level `dopemux` CLI exposes **no** `pcp bridge`, `bridge mutate`, or live-write commands.
- `python -m dopemux.pcp.cli export --help` is the supported read-only PCP CLI entry.

## LIVE_WRITE_READY gates

- Schema-valid `READY` is **not sufficient** for activation.
- Any production writer requires a **trusted issuer verifier** injected at bridge/router construction.
- Unsigned or self-asserted READY objects are rejected when a writer registry is active (`ASSERTION_ISSUER_UNTRUSTED`).
- Approval, audit, and allowlist fields are **presence-checked by schema**; truthfulness is verified by issuer/provenance, not schema alone.

## Authority binding

- Writers require a **SOURCE** authority-map entry with `live_write_allowed=true`, matching `target_surface` and `canonical_writer`.
- Derived surfaces (`ADAPTER`, `PROJECTION`, `MIRROR`, `CACHE`, `INDEX`, `UNKNOWN`) cannot write.

## Dedup

- Bridge idempotency uses a pluggable **`dedup_store`** (`InProcessDedupStore` or `RedisDedupStore`).
- **Distributed dedup** (Redis SET NX) is required for multi-replica activation.

## DCP proof family

- `schemas/dcp_extension/proof_family.dcp.json` is a **projection-only** mapping to PCP proof pointers.
- `is_authority=false`, `projection_only=true`, `unknown_behavior=BLOCK_OR_ESCALATE`.
- DCP proof family does **not** own generic PCP proof semantics.

## Routing contracts

- DCP route-decision schemas are **contracts-only** until runtime activation.
- `SELECTED` routes cannot carry unknown provider/model/runner.
- OpenRouter free paths are forbidden for private/security/release/schema-authority lanes.

## PR Steward

- Generic PR Steward output is **advisory** and is **not** merge authority.
- `intake_completeness` must be `COMPLETE` for every required category before `READY`.
- Green CI is **not** semantic proof.
- Unknown/missing evidence blocks or escalates.
