---
id: local-project-supervisor
title: Run a bounded local project mandate
type: how-to
owner: '@hu3mann'
author: Codex
date: '2026-10-16'
last_review: '2026-10-16'
next_review: '2027-01-14'
prelude: Trusted deterministic commands, finite repairs, private local delivery and conservative recovery.
---
# Run a bounded local project mandate

Use this local candidate only for trusted, reviewed deterministic commands under an
already approved outcome. Current canonical MacroPackets, child Task Packets and
ExecutionBindings remain required upstream. A manifest or authorization reference does
not authenticate them. See [architecture](../systems/supervisor/architecture.md) for actual
mechanisms and [adoption](../04-explanation/architecture/full-system-r2/adoption.md) for review history.

## Prepare one finite outcome

Choose an isolated canonical project/worktree and private current-UID state/return roots
outside every project. Existing state/return directories must be mode 0700 and have no
symlink ancestry; the runtime rejects permissive custody rather than changing permissions.
Use an already installed compatible Python and source checkout. The lean module entrypoint
avoids ordinary application CLI startup, dotenv/configuration and provider imports.

Copy the [v1 template](../../examples/supervisor/project-mandate.template.json) into approved
private custody. Replace every `REPLACE`, both zero expiry timestamps, exact executable
and argv, project paths and receipt labels with actual owner-bound values. Gates must
come from independently verified current evidence. Never mark an unknown gate PASS.
The [v1 schema](../../schemas/supervisor/project-mandate.v1.schema.json) checks shape;
[mandates.validate](../../src/dopemux/supervisor/mandates.py) adds semantic validation.

A mandate lists 2–32 implementation, test/validation and optional known-failure repair/retest
steps. Every step can be claimed at most once. `repair_limit` is at most two; repairs consume
the original attempts, active budget and expiry. Successful validation leaves its repair
branch dormant. There is no automatic parser retry or harness repair. `success_steps` names
alternative validation predicates; implementation must also succeed. Completion still needs
separate native acceptance. Local spend must be zero; this adapter has no provider cash meter.

## Admit and execute

From the source root, replace these illustrative paths with the approved write cone:

```sh
export PYTHONPATH="$PWD/src"
python3 -B -m dopemux.supervisor --state-root /approved/private/state \
  --return-root /approved/private/returns --receiver-ref local-operator \
  admit /approved/private/mandate.json --authorization-ref native-verified-reference
python3 -B -m dopemux.supervisor --state-root /approved/private/state \
  --return-root /approved/private/returns --receiver-ref local-operator run
```

Admission commits mandate, grant, qualified binding, works and outbox in one local SQLite
transaction. It does not make subprocess or filesystem effects database-atomic. Identical
re-admission preserves limits and counters. Changed identity requires an explicit successor;
it cannot silently replenish an allowance. `run` exits 0 for completion pending native
acceptance, 3 for a hold, 4 for unfinished/blocked and 2 for malformed input/local I/O failure.
Inspect structured status and evidence even after nonzero exit.

## Portfolio and live control

Admit disjoint projects into the same state root. Their immutable grants, budgets and
qualified routes remain separate. Project/root writer keys, named resources and a shared
heavy slot prevent overlapping work within this journal. Up to two eligible local commands
can run concurrently. An incomplete historical admission holds its own project. Separate
journals do not share a physical custody fence; do not use them for overlapping outputs.

A coordinator file lock excludes competing admission/recovery/run commands. Current local
owner narrowing uses a short SQLite transaction and works while that coordinator runs:

```sh
python3 -B -m dopemux.supervisor --state-root /approved/private/state \
  --return-root /approved/private/returns --receiver-ref local-operator \
  control mandate-id --sequence 1 --receipt-ref local-owner-denial \
  --action deny --gate security
```

Use increasing sequences and immutable receipt refs. `revoke` and declared `stop` conditions
are also supported. All controls are monotonic holds; no PASS, release or allowance reset is
available. The actual local UID is recorded, not accepted from a caller field. This same-account
interface is not a cryptographic Native identity or cloud owner bridge. Legacy `observe-gates`
requires an idle coordinator and cannot erase a mandate-level hold.

## Local delivery and evidence

Per-attempt `stdout.log`, `stderr.log`, `START_ACK.json` and `PROCESS_RESULT.json` stay beneath
private `state/evidence`. After a successful local child exits, `Runtime.run` validates its
actual running attempt/fingerprint, native exit/closure and capture identities. It publishes
an immutable `STEP_BOUNDARY_CHECKPOINT.json` binding the native evidence bytes, then records
a kernel `CHECKPOINT` before finishing the step. Failed or unconfirmed children do not create
a successful checkpoint. Original result-reference ordering is unchanged.

Intent precedes launch; compact work events and project deltas enter a durable outbox.
Immutable files use SHA-256 identity and coordinated fsynced publication. Retrying delivery
never launches work. A checkpoint records observed child evidence, not native acceptance or
proof that the kernel step has finished.

```sh
python3 -B -m dopemux.supervisor --return-root /approved/private/returns \
  --receiver-ref local-operator receive
python3 -B -m dopemux.supervisor --state-root /approved/private/state \
  --return-root /approved/private/returns --receiver-ref local-operator deliver
```

`receive` writes up to 100 `LOCAL_DELIVERY_RECORD` files per call. They bind exact key/digest,
receiver label and actual UID, with Native acceptance and Master ACK `NOT_ASSERTED`. Legacy
`acks/` files are ignored. `deliver` settles only matching local records. A real cloud bridge
must independently authenticate upstream roles; no bridge is installed. Transient transport
I/O preserves pending events while independent work continues; conflicting immutable data
holds its affected project. Queue archive/rotation/backpressure is deferred.

## Synthetic owner-admission check

The separate owner API reuses the unchanged canonical GEC validator and MCP identity resolver.
Its only supplied port is an explicit protected synthetic fixture. Against a pre-created fixture
and exact request, the complete CLI shape is:

```sh
python3 -B -m dopemux.governed_execution.admission check-fixture \
  --owner-root /approved/private/synthetic-owner \
  --request /approved/private/synthetic-request.json
```

See [interfaces](../systems/supervisor/interfaces.md) for fields and typed errors. Fixture
output always says `fixture_only: true` and `execution_authorized: false`. It is not consumed
by local dispatch. Missing real owner bindings fail closed; copying a schema-valid receipt or
supplying a matching digest cannot create native authority. Portable v2 projections do not
enable v2 execution or replace the canonical GEC artifact family.

## Recovery and practical limits

Reopen the same journal. Original deadlines, counters and successful attempt evidence remain.
A changed monitored project view holds work. Interrupted RUNNING or cancelled work becomes
EFFECT_UNKNOWN with output/heavy custody retained; no automatic retry follows. Trusted
`reconcile` and `record-acceptance` APIs record evidence verified elsewhere, but do not
independently prove process closure or authenticate native receipt strings. Stop release,
rebaseline and reuse ancestry have deferred limitations.

The kernel exposes checkpoints; the local runner does not save mid-command checkpoints.
The runtime now records step-boundary checkpoints only after child completion. Interruption
before checkpointing, or after checkpointing but before finish, retains unknown effects on
restart; a saved checkpoint never automatically promotes or retries that step. Interruption
after finish preserves the completed step for idempotent return delivery without reexecution.
Missing/mismatched native evidence or conflicting immutable checkpoint bytes fail closed.
Captures are bounded (default combined 128 KiB, maximum 1 MiB); truncation holds the result.
Processes use replacement environments and fresh process groups with bounded cooperative
cleanup. Cancellation is not proof of closure. Slow snapshot accounting, orphan closure and
effect-time executable/root drift remain deferred. Active time sums command durations;
parallel work consumes aggregate duration, not portfolio wall time.

This is not an OS/network/filesystem sandbox. Visible write detection has hidden/cache/vendor
blind spots and cannot undo effects. Children retain the host account and enclosing sandbox's
permissions. Run only qualified deterministic commands; no credentials, external effects,
paid calls or hostile code. No Codex, Claude, Grok, AGY, Command Code or OpenCode model adapter,
service daemon, distributed lease or canonical admission installation is supplied.

Use the [runbook](../systems/supervisor/runbook.md) for focused test commands and failure handling,
and [migration](../systems/supervisor/migration.md) before any authorized integration. Preserve
unknown effects, exact ownership and evidence during rollback; avoid broad reset/clean.
