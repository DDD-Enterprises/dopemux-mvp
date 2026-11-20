---
id: full-system-r2-adoption
title: Full-system R2 first-wave adoption record
type: reference
owner: '@hu3mann'
author: Codex
date: '2026-10-16'
last_review: '2026-10-16'
next_review: '2027-01-14'
prelude: Exact candidate inputs, path decisions, spent review history and remaining gates.
---
# Full-system R2 first-wave adoption record

This record binds the W00/W01/W23-S1 implementation candidate. It records owner decisions
supplied to the worker; it does not write a canonical owner ledger or assert final acceptance.

## Bound inputs and approved path decisions

- Native mandate: `DMX-FULL-SYSTEM-R2-W00-W01-W23S1-IMPLEMENTATION-20261016-R1`.
- Master match: `MCT-DMX-FULL-SYSTEM-R2-W00-W01-W23S1-IMPLEMENTATION-MATCH-20261016-R1`.
- R2 source: private Library `libfile_9e35accf2a8c81919f01e5e84f27d7ce`, version 0,
  `FULL_SYSTEM_ARCHITECTURE_R2_DESIGN_20261016.zip`, 1,063,643 readable bytes,
  SHA-256 `49955eca5c43568199e3f3a6bfa84ffb3ed6688d13ed113dab4afd2cb009cf5e`.
- Git base: `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`.
- Imported frozen 22-file failed overlay patch:
  `f9b577370333f16a9870ea2a5824ae7570e955b65703ef8e8c5ba5f77c035d27`.
- Prospective 36-path ownership manifest:
  `eab9e84e8b0fc255ade2a9e607b42dd9e71dd7aad3cac7fb59e0dce63f75187c`.

The approved owner-admission path is
`src/dopemux/governed_execution/admission/owner_admission.py`, ahead of the unchanged
canonical GEC validator. Do not introduce the conflicting supervisor-local alternative.
The approved portable mandate schema spelling is `schemas/supervisor/project-mandate.v2.schema.json`.
Its Draft 2020-12 common bundle remains separate from the canonical GEC Draft 7 registry
and the strict deterministic local v1 contract. These resolve the source BUILD_PLAN's
header/write-set inconsistency explicitly.

The single worker uses a separate detached build worktree. The primary checkout, original
reviewed candidate, Master sources, GEC validator/store/join, identity resolver/registry,
PM/TO state and S2/S3 documentation remain unchanged. Fixture owner records are synthetic
and never installed as genuine native records. No commit, publication, merge or activation
is part of this wave.

## Current result and proposed target

The [S1 architecture](../../../systems/supervisor/architecture.md) and
[interfaces](../../../systems/supervisor/interfaces.md) identify implemented symbols and tests.
The portable contract bundle is adopted as this candidate's schema input, not as enabled
v2 runtime execution. Only a synthetic owner port is supplied; real owner integration
fails closed until its actual native binding exists. Local same-account narrowing and
receipt records provide no cross-domain role authentication.

W23 S2/S3 remains separately owned at repaired subject `S2-REPAIR-1-20261016`, with pinned
47-file manifest `7fbb3c684cf234507b8a0c929505a550d1fe5e41eefdd8e4a9ea24a4ad3272a9`.
Its earlier independent REPAIR_REQUIRED and pending successor review remain intact.
Structural inventory comparison retains all 91 prior components and 89 prior edges; R2
adds two source variants and three alias/source-variant edges. This is a source comparison,
not a claim of deployed services or complete documentation facets. No duplicate S2/S3 manual
is created here. The existing dispatch guard is reused only as advisory validation preflight;
its metadata never authenticates an execution grant.

## Review history and finding disposition

The original four-file/31-test candidate failed independent L2. The later review002 also
returned FAIL (1 HIGH, 10 MEDIUM, 4 LOW), consuming its one authorized independent review.
The separate API-EPERM/no-verdict audit attempt remains spent; an expired earlier canary
was closed as recovery-only, without retroactive PASS. No new audit is authorized here.

| Review002 finding | First-wave treatment / later owner |
|---|---|
| F01 atomic admission | local database transaction + stage fault tests |
| F02 ACK provenance/custody | LOCAL_DELIVERY_RECORD, private UID roots; cross-domain ACK deferred W03 |
| F03 publication/isolation | coordinated publication/read, per-project conflicts, transient I/O pending |
| F04 process/orphan closure | deferred W06/W02; process runner unchanged |
| F05 live narrowing | ordered local-UID deny/revoke/stop during run; real owner bridge deferred |
| F06 stop release/rebaseline | deferred W02 |
| F07 slow hashing/time accounting | deferred W06/W02 |
| F08 evidence integrity | deferred W09/W03 |
| F09 cross-journal physical custody | deferred W02 |
| F10 executable/root drift and monitor blind spots | deferred W06/W08 |
| F11 doctrine claims | current mechanisms, projections and deferred work distinguished on touched surfaces |
| F12 strict input | typed first-wave malformed input, duplicate/nonfinite rejection; no whole-system claim |
| F13 reuse ancestry | deferred W02 |
| F14 queue retention/backpressure | deferred W03 |
| F15 validation evidence | focused negative/CLI/fault/concurrency coverage and exact-subject freeze |

Local test success is author evidence only. It does not close deferred findings, grant
controlled integration or replace final independent review/native acceptance. The final
candidate manifest and command receipts are separate frozen deliverables; no self-hash
or invented receipt appears in this source record.

## Remaining gates and dependencies

W02 must establish physical custody and recovery across journals. W03 must authenticate
role-bound Native/Master ACKs and queue lifecycle. W04 owns canonical PM/TO transitions:
current PM writes can overstate legality/version/persistence/SYNCED, and `pm_log_progress`
can discard an async ConPort call. W06/W08/W09 own harness/process qualification, effect-time
identity and integrity. This first wave does not repair those runtime paths through prose.
Model adapters, actual cash meters, durable runner checkpoints and production v2 dispatch
remain unimplemented. Separately authorized exact-subject review and owner integration
approval are required before landing/activation. See the [migration procedure](../../../systems/supervisor/migration.md).
