---
id: supervisor-interfaces
title: Local supervisor interfaces
type: reference
owner: '@hu3mann'
author: Codex
date: '2026-10-16'
last_review: '2026-10-16'
next_review: '2027-01-14'
prelude: Entrypoints, projections, local state and authority limits.
---
# Local supervisor interfaces

## Entrypoints and authority

| Interface | Current behavior | Authority boundary |
|---|---|---|
| `python -m dopemux.supervisor ... admit FILE --authorization-ref REF` | validates strict local v1 and atomically records technical admission | trusted operator must already verify current canonical packets/bindings; REF is a label |
| `run`, `status`, `deliver` | local scheduling, inspection, retryable outbox delivery | no upstream issuance or remote calls |
| `receive` | up to 100 `LOCAL_DELIVERY_RECORD` files per batch | current UID receipt; native/Master ACK `NOT_ASSERTED` |
| `control ID --sequence N --receipt-ref REF --action deny --gate security` | short SQLite transaction, current local UID, monotonic mandate hold | narrowing only, works during a coordinator run |
| `control ... --action revoke` | permanently narrows this grant to revoked | no unrevoke/regrant |
| `control ... --action stop --condition CONDITION` | records a declared project stop | no stop release |
| `observe-gates` | legacy trusted library/idle CLI observation | does not bypass a mandate hold; CLI requires idle coordinator |
| `record-acceptance`, `reconcile` | record externally verified evidence through trusted local APIs | strings do not authenticate that evidence; future integration required |
| `python -m dopemux.governed_execution.admission check-fixture --owner-root ROOT --request FILE` | offline explicit synthetic fixture inspection | `fixture_only: true`, `execution_authorized: false` |

The lean module CLI avoids the ordinary application CLI's configuration/dotenv startup.
No command installs dependencies, starts a service or selects a live model.

## Owner port

[OwnerAdmitter](../../../src/dopemux/governed_execution/admission/owner_admission.py)
accepts an `OwnerResolver` trusted application port, an exact four-field EvidenceRef,
principal, typed `ExpectedScope` and expected generation. A caller-supplied JSON owner
object cannot replace that port. The explicit `LocalOwnerResolver(..., fixture_mode=True)`
loads a synthetic protected `owner.json`, mapped canonical source bytes and an existing
fixture identity registry. Without explicit fixture mode it fails `E_ISSUER_UNAVAILABLE`.
It never creates or amends a real owner ledger.

`ExpectedScope` binds project/workspace/instance/worktree/actor/client, macro/packet/subject,
effects/resources/routes, active/wall/spend/attempt/repair/parallel/delegation limits,
expiry and policy/trust/schema digests. Child scope must be an intersection of that
owner scope. Recheck resolves current generation, revocation and expiry again. Actual
execution does not consume these synthetic admissions; no bridge to `Runtime.admit` exists.

Errors are typed `AdmissionError` codes: schema/version, unavailable issuer, authenticity,
role, stale/revoked generation, identity/custody, scope/policy and source drift. Malformed
JSON rejects duplicate keys and nonfinite numbers. Unknown portable versions do not
fall through to v1. Fixture CLI emits structured error JSON and exits 2 on rejection.

## State and events

The local SQLite projection stores grants, routes, works and project stops. `mandates`
stores immutable v1 inputs and monitored baselines. `outbox` stores stable key, project,
payload, digest, created timestamp and legacy `acked` timestamp; the latter means local
delivery settlement only. Canonical PM/TO/decision state remains elsewhere.

Work events carry key, kind, work/project/grant/attempt/route identity, status, input
fingerprint, evidence references and `authority: NONE`. Aggregate `PROJECT_RETURN` events
carry per-project state and a journal reference. Their key derives from immutable payload
identity. Delivery retries never dispatch work. Native acceptance remains separate.

A local delivery record contains kind `LOCAL_DELIVERY_RECORD`, exact key/digest,
receiver label, actual `recorded_by_uid`, `native_acceptance: NOT_ASSERTED` and
`master_ack: NOT_ASSERTED`. Old `acks/` files are ignored. Same-account matching files
are not cryptographic or cross-domain evidence.

`owner_control` and its receipt history live on the affected grant. They bind increasing
sequence, immutable receipt ref, actual UID, action and optional gate/stop condition.
Exact repeated receipt is idempotent. Stale/conflicting sequences reject. Every supported
control holds the mandate monotonically; later observations cannot restore authority.

## Schema editions

The existing [local v1 schema](../../../schemas/supervisor/project-mandate.v1.schema.json)
continues to mean deterministic `local_command`, zero paid spend, 2–32 listed steps,
parallel ceiling two and ordinary-repair ceiling two. The runtime adds semantic validation.

The six new portable files under `schemas/supervisor/` are copied from the approved R2
contract bundle. `full-system-contracts.v1.schema.json` is Draft 2020-12; dotted wrappers
reference its mandate, admission, identity, subject and governance definitions. Projection
checks resolve only bundled local definitions with date-time format checks. The canonical
GEC Draft 7 registry and pure join are unchanged. Parser ceilings never issue a grant.
