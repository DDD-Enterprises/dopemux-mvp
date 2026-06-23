---
id: PCP-FASTAPI-BRIDGE
title: PCP FastAPI Bridge / Live-Write Adapter
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: PCP FastAPI Bridge / Live-Write Adapter (explanation) for dopemux documentation
  and developer workflows.
---
# PCP FastAPI Bridge / Live-Write Adapter

The PCP live-write bridge (`src/dopemux/pcp/bridge/fastapi_bridge.py`) is an
**inert-by-default adapter** that can route a mutation to a registered canonical
writer **only behind a satisfied, authenticated `LIVE_WRITE_READY` gate**, with
dry-run first and fail-closed semantics.

It is an **adapter, never a canonical authority**: every result carries
`is_authority: false`, and `executed` is true only when a live write actually
ran. The bridge performs no I/O of its own and wires none of the forbidden
live-write runtimes (AIR Red Line #15).

## Fail-closed decision

`route_mutation(operation, *, live_write_ready, execute, writer_registry, dedup_store, assertion_verifier, authority_binding, now)`
evaluates, in order. A writer is reached only at the final step; every other
branch returns without invoking any writer.

| Step | Condition | Result if it fails |
|---|---|---|
| 1 | `operation` is a dict with non-empty `operation_ref` + `target_surface` | `REJECTED` (`MALFORMED_OPERATION`) |
| 2 | gate validates against the schema, is `READY`, consistent, and unexpired | `REJECTED` (`GATE_ABSENT` / `GATE_SCHEMA_INVALID` / `GATE_NOT_READY` / `GATE_INCONSISTENT` / `GATE_EXPIRED`) |
| 3 | gate `operation_ref` + `target_surface` equal the operation's | `REJECTED` (`GATE_OPERATION_MISMATCH`) |
| 4 | `sha256(canonical(operation))` equals gate `payload_digest` | `REJECTED` (`PAYLOAD_DIGEST_MISMATCH`) |
| 5 | `execute is True` (identity, not truthiness) | `DRY_RUN` (no write) |
| 6 | gate's `canonical_writer` name resolves in `writer_registry` | `REJECTED` (`CANONICAL_WRITER_NOT_REGISTERED`) |
| 7 | assertion verifier PASS (required when writer registry active) | `REJECTED` (`ASSERTION_ISSUER_UNTRUSTED` / verifier reasons) |
| 8 | authority-map SOURCE binding PASS (required when writer registry active) | `REJECTED` (`AUTHORITY_MAP_ABSENT` / binding reasons) |
| 9 | `assertion_id` is first-seen in `dedup_store` | `REJECTED` (`DUPLICATE_SUPPRESSED`) |
| 10 | writer returns normally | `LIVE` on success; `REJECTED` (`WRITER_RAISED:<type>`) on exception |

Modes map to HTTP status on `POST /bridge/mutate`: `REJECTED` → 403, `DRY_RUN` /
`LIVE` → 200. The endpoint is thin — all logic lives in `route_mutation`.

## No default writer

`create_bridge_router(*, writer_registry=None)` defaults to **no registry**, so a
deployed app can never perform a live write — every `execute` attempt resolves no
writer and is rejected. The writer is resolved **by the gate's `canonical_writer`
name**, not by an arbitrary injected callable; registering a real writer is an
explicit, deliberate operator action. This is what technically enforces AIR Red
Line #15 (the forbidden `queue_drain execute=True` / `batch_resolve_and_merge`
runtimes can never become the bridge's writer unless deliberately registered
under the gate's approved name) and closes canonical-writer substitution.

## Hardenings beyond the bare gate

These close the gaps an adversarial review identified for a live-write surface:

- **TTL** — the gate's `valid_until` is enforced (`now > valid_until` → `GATE_EXPIRED`); a stale assertion cannot authorize a write.
- **Payload binding** — `payload_digest` binds the assertion to the exact operation payload, not just its `operation_ref` / `target_surface` (closes confused-deputy / replay against a different resource). Gate authors must compute it as `sha256(json.dumps(operation, sort_keys=True, separators=(",", ":")))` with default `ensure_ascii=True`; a different encoding produces a (fail-closed) `PAYLOAD_DIGEST_MISMATCH`.
- **Assertion authentication** — when a writer registry is active, an injected `assertion_verifier` must PASS; default is fail-closed (`NoTrustedIssuerVerifier`).
- **Authority-map binding** — when a writer registry is active, `authority_binding` must authorize the `target_surface` + `canonical_writer` pair against a SOURCE entry with `live_write_allowed=true`.
- **Idempotency dedup** — the bridge records each `assertion_id` in `dedup_store` before the write; a replayed assertion is `DUPLICATE_SUPPRESSED` (in-process per router, or Redis for multi-replica). If the writer raises after the key is recorded, the assertion stays suppressed — a retry requires a fresh `assertion_id` (a failed write is never auto-retried).
- **Canonical-writer registry** — the gate's named writer must map to a registered callable.

The `valid_until` + `payload_digest` fields were added to
`schemas/project_control_plane/live_write_ready.schema.json` (required + format-checked
under the READY gate; optional for non-READY assertions). The schema version
stays `pcp.live_write_ready.v0` — the contract has no production consumers yet, so
the additive hardening is pre-use rather than a breaking version change.

## Deferred (out of scope here)

These remain the responsibility of the assertion's production path and the
operator runbook, not this bridge:

- **Production issuer/key material** — must be configured out-of-band; the bridge ships a fail-closed verifier scaffold only.
- **Distributed / cross-process dedup** — use `RedisDedupStore` for multi-replica activation; in-process dedup is test/single-worker only.
- **Allowlist + auditor-independence** are self-reported in the assertion and verified out of band (AIR Red Line #9); the bridge enforces field presence via schema/gate checks, not semantic truthfulness.
