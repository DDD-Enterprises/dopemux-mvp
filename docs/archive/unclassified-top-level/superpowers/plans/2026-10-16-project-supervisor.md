---
id: project-supervisor-vertical-slice-20261016
title: Project supervisor vertical slice
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-10-16'
last_review: '2026-10-16'
next_review: '2027-01-14'
prelude: Local tested supervisor kernel implementation scope and remaining integration boundaries.
---
# Project supervisor vertical slice — 2026-10-16

Owner decision relayed at 04:21:38 UTC: "adopt all and update dopemux supervisor implementation".
Execution method: this existing task implements a local, additive slice; no provider/model child, browser, VM, live worker, service, canonical-state migration or publishing.
Base: 95e95bee88cae5e6c95e6e34f7c28bb423ad9496. Isolated root: /Users/hue/Documents/Codex/2026-10-14/task-10/supervisor-worktree.
Primary checkout has unrelated instruction/config changes; do not copy, stage or alter them. PR1430 excluded.

Approved investigation basis: task-10/proposal.md and contracts.md, bounded grants/checkpoints/idempotent deltas.
The source has execution models/in-memory leases, GEC dispatch qualification and evidence storage.
It does not have this project-supervisor loop. Existing leases and GEC contracts remain unchanged.

## Implementation child — additive local kernel
Create src/dopemux/supervisor/{__init__.py,kernel.py}.
One trusted local coordinator consumes already-admitted project grants and route bindings.
SQLite transactions persist grant reservations, work transitions, evidence refs and an outbox.
One project grant authorizes routine steps within scope; do not create command/read/metadata microgrants.
Select ready independent work immediately, prefer eligible Sol routes unless pinned, exclude shared writers.
Preserve expiry, active time, worst-case spend reservation, stop conditions, required gate receipts and no-VM.
Execution intent commits before an injected runner is invoked. Unknown effects retain reservations/custody; never auto-replay.
Unchanged input/evidence and duplicate acknowledgments reuse durable results.
Completion is distinct from native acceptance. Trusted native acceptance references count accepted capability.
No live runner or self-attesting grant authenticator is installed by this slice.

## Validation child — deterministic contract and integration tests
Create tests/unit/supervisor/test_kernel.py.
Use stdlib unittest with fake async runners and private temporary SQLite files; no project app/service imports.
First run must fail because the new kernel is absent.
Cover persisted bounds/revocation, uncertain-effect no replay, writer exclusion, independent scheduling/backfill,
duplicate/outbox conflict handling, evidence reuse, gate holds, eligible-route pin/preference,
acceptance vs completion and elapsed/spend/return-ack-wait metrics.
Command: PYTHONPATH=src python3 -B -m unittest discover -s tests/unit/supervisor -v.
Run git diff --check and bounded syntax checks. Use existing installed tools only; no dependencies installed.
Required repo contract/hook checks are evaluated separately; report unavailable tooling and no full-suite claim.

## Integration status and acceptance
Update this plan with actual checks and limitations. This is importable local code, not an installed daemon/CLI,
provider-capability qualification, OS sandbox, signed authority verifier or canonical workflow owner.
Production exposure, GEC adapter integration and any required independent final audit remain separate.

## Implemented checkpoint

The isolated worktree now contains the local kernel and 31 deterministic tests.
`Supervisor.admit(Grant)` consumes a project-level outcome envelope supplied by a
trusted adapter; routine work uses `enqueue(Work)` without command/read/metadata
microgrants. `bind_route` caches admitted route references until expiry or explicit
invalidation. An unpinned eligible set prefers the `sol` class; a one-route pin
is retained. These labels do not establish provider identity or invoke a model.

`run_ready(fake_or_qualified_executor)` claims independent work transactionally and
backfills freed slots without waiting for slower peers. Writer resources and one
host-heavy resource serialize conflicting work. Intent, active-time and worst-case
cash reservations commit before the injected executor is invoked. Expiry,
revocation, current gates and route invalidation stop cooperative execution.

Checkpoints and result events enter a SQLite outbox automatically. Identical
input/evidence/result/ACK deliveries reuse prior state; conflicting bytes fail.
`flush_returns(already_authorized_sink)` sends stable bounded envelopes and accepts
only matching digest ACKs; ACK loss leaves the same return pending and never
reexecutes the workload. Returns are at most 16 KiB, delivery batches 100 events,
work/context metadata at most 16 KiB. Neither method contacts Master by itself.

`accept` records a trusted native acceptance reference separately from execution
success. Metrics expose distinct accepted capability IDs, project elapsed time,
active seconds, settled/reserved spend, and acknowledged return-to-ACK wait. The
wait metric sums per-event intervals; it is not a disjoint decomposition of
elapsed time or a measured savings claim. Unknown and in-flight spend stays null.

Harness repair is counted inside the same grant and unchanged inputs. Two matching
failure signatures hold the stage; exhausted repair or active-time allowance
cannot renew itself. This permits local parsing/harness correction only; there is
no automatic model resubmission, failed-stage retry or new grant issuance.

Interrupted/ambiguous work remains EFFECT_UNKNOWN with custody/reservations held.
Recovery never requeues RUNNING work; it only records a hold. There is deliberately
no inferred zero consumption, TTL takeover, refund or blind replay.

## Integration limits and next gate

The kernel is an importable library, not an installed supervisor, daemon or CLI.
Local callers are trusted. Grant/gate/native-acceptance references and binding
labels are not cryptographic authentication. No model-returned dictionary should
be admitted directly. A subsequent native adapter must authenticate current
upstream scope/workflow/security/spending/public-release evidence and bind exact
filesystem effects, route/capability provenance and actual writer custody.

The asyncio timeout/stop path controls cooperative coroutines only. It does not
enforce OS process termination, credential isolation, network restrictions or a
provider's cash limit. Real adapters must enforce their declared limits and return
native lifecycle evidence; otherwise live dispatch stays held. In particular,
the Python callback interface must not be treated as a security sandbox.

Use one coordinator for run/recovery per journal. SQLite serializes claims across
connections, but this slice does not authenticate a second coordinator or provide
distributed fencing. Scope/resource names are adapter-owned registry references,
not a new canonical project registry or a filesystem isolation mechanism.
No legacy/canonical store is initialized or migrated. No current runner API is
assumed. No global credentials, security settings, VM or browser access is used.

The repository change-contract preflight classifies this as L2 and requires a
final independent audit before readiness. The original frozen four-file candidate
subsequently received FAIL (1 HIGH, 4 MEDIUM, 5 LOW) in independent audit
`DMX-PROJECT-SUPERVISOR-R1-INDEPENDENT-L2-20261016-001`.
This document describes that historical library checkpoint. The successor plan
`2026-10-16-supervisor-permanent-integration.md` and local supervisor quickstart
describe the later CLI, gate/reconciliation and runner integration. The failed
audit does not certify the successor. Its new formal audit is not issued.
The exact original source and patch remain frozen outside this checkout.
No production wiring, commit, push, merge or release is included.
