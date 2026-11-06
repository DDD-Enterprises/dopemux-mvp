---
id: project-ownership-v2
title: 'Project ownership v2: source-only implementation'
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-11-04'
last_review: '2026-11-04'
next_review: '2027-02-02'
prelude: Canonical project ownership, isolated validation, checkpoint recovery and remaining live activation gates.
---
# Project ownership v2: source-only implementation

The owner adopted the project-ownership v2 contract on 2026-11-04 for isolated
implementation. This does **not** admit a live project or enable a production
writer. Runtime transitions are exercised only with temporary stores and injected
fixture verifiers. Production authentication, source allocation, storage and
destination channels remain qualification gates.

## Authority and composition

The existing IdentityRegistry issues project/workspace/instance identifiers. PM
admission grants domain access to an existing identity; it never registers one.
One `SQLiteTaskStore` owns one project, database, store UUID and lifetime OS lock.
`CanonicalTaskRuntime` is explicitly injected through a lifespan factory. Missing
composition yields 503; its default principal and completion verifiers deny access.
The ordinary service startup does not discover or create a canonical PM database.

The runtime reads only BOUND tasks from that store. Operator migration staging is
separate. Task lookup identity is `(project_id, task_id)`; legacy ID bytes are
preserved. New IDs use the adopted NUL-separated SHA-256 identity tuple. Native
creation requires a producer's stable, persisted operation UUID.

Registry membership, request actor strings, localhost, process environment and
URL paths do not grant ownership. A server-injected `PrincipalVerifier` authenticates
the canonical method/route/project/operation/body binding. The writer rechecks
expiration, exact audience, verifier, current credential generation, client and
named action inside the transaction. No production provider is included here.

## Canonical operations

The v2 router exposes:

- `POST /api/v2/projects/{project_id}/workflow/tasks`: strict task creation.
- `POST /api/v2/projects/{project_id}/workflow/transition`: strict versioned command.
- `GET /api/v2/projects/{project_id}/workflow/tasks/{task_id}`: authorized task view.
- `GET /api/v2/projects/{project_id}/workflow/state`: scoped counts, queue and
  advisory capabilities, with explicit pagination.
- `GET /api/v2/projects/{project_id}/workflow/receipts`: original receipt by
  `operation_kind` and `idempotency_key`, scoped to the authenticated principal.

Transition fields are all explicit: schema version, task ID, transition, expected
task and binding versions, admission epoch, idempotency key, nullable reason and
nullable completion reference. Unknown fields, duplicate JSON keys, coerced
versions and invalid Unicode scalars reject before effects. Commands are capped
at 64 KiB at HTTP ingress. The request/receipt schemas and pinned byte vectors are
under `schemas/pm/ownership-v2/`.

Start is TODO → IN_PROGRESS; resume is BLOCKED → IN_PROGRESS with a nonblank
reason; block is TODO/IN_PROGRESS → BLOCKED; done is IN_PROGRESS → DONE with a
nonblank reason and verified completion reference. Each requires its named grant.
Start/resume require every dependency to be DONE with recorded completion evidence.
A new key cannot repeat a no-op block. Cancel, rehome, metadata/link/dependency
edits and network administration are unavailable.

Every accepted operation atomically records the journal, task/policy projection,
original receipt and outbox. A key is scoped by project, principal and operation
kind. The digest includes the complete semantic command and stable client identity.
Exact replay returns the original receipt even after subsequent transitions or
an admission epoch change, provided current authorization still allows it. A
different client conflicts on mutation replay but can query the original receipt
with a current read grant. Revoked principals cannot retrieve it. Suspended
admissions deny mutation replay; explicit current read grants can still read.

Clients must validate the actual receipt's project, task, actor, digest, versions,
binding and legal state pair, including the requested evidence digest for DONE.
They must never synthesize `expected_version + 1`.
The v2 adapters have no response cache, retries, provider discovery or downgrade.
Legacy v1 project workflow reads/transitions and local-first PM writers are held.
Legacy bridge lifecycle emitters cannot manufacture canonical completion events.
Existing noncanonical demo stores are not converted into admitted authorities.

## Completion evidence

`KernelCompletionVerifier` receives trusted task/workflow/policy bindings and
immutable canonical snapshot bytes at composition. A snapshot includes the exact
project/task/version/source identity/revision, workflow state and base64 artifact
contents. Its reference digest covers those bytes. No caller filesystem path is
opened. Artifacts are materialized only in a temporary contained directory, then
checked with the existing workflow kernel's phase and artifact gates.

The adapter requires a matching refactor checkpoint, approved research/plan review,
completed implementation, nonempty required task artifacts, and workflow-wide
requirements when the binding selects workflow scope. Completion proves evidence
shape and presence. It does not prove code correctness, an independent audit or
release acceptance. Malformed nested workflow, task, checkpoint, required-artifact
or artifact/base64 shapes are rejected before coercive workflow parsing and become
`completion_unavailable` before a transaction or operation-key consumption. Only
expected sealed-input parse failures are normalized; arbitrary injected verifier
bugs remain visible. The writer preserves the sealed snapshot in the journal and
rechecks task/policy version before commit. DONE is not advertised by a read that
has no exact evidence reference.

## Local maintenance and migration

`python -m dopemux.pm.maintenance` is a local operator entry point, not a network
tool. It requires explicit paths and an out-of-band approved SHA-256. Bundles,
stores and checkpoints require operator-owned regular files, private parent
directories and no symlink traversal. The runtime must close before maintenance
can acquire the same exclusive lock.
Host shutdown first rejects new runtime requests and drain calls, waits for an
existing delivery pump, and closes the store under its transaction mutex. The
writer lock is released only after in-flight commits and checkpoints finish.
Destination adapters must have bounded calls and must not invoke runtime shutdown
from inside their delivery callback; shutdown belongs to the composing host.

Supported commands are `dry-run`, `bootstrap`, `replace-admission`, `import-bound`
and `reconcile`. No command is run against a live store by the source tests.

An admission bundle names the exact registry snapshot/generation/chain, complete
active-admission/source/legacy allocation inventory, grants, source mappings,
versioned completion policies and destination IDs. Bootstrap requires an absent
database. Policy replacement is complete, increments the epoch and preserves
project/store/writer identity. Replacement preserves every known admission,
source allocation and legacy allocation; old allocation keys cannot disappear or
be reassigned. Its inventory revision cannot regress. A changed inventory requires
a newer revision; equal revision is allowed only for identical effective inventory
(including order-independent allocation content). Existing tasks retain their source
system/instance/external-project mapping and exact completion policy. Grants and
producer access may be revoked and admission may be suspended independently.
Registry bytes are rechecked at the commit boundary.

The effective inventory is derived during journal replay: a deterministic immutable
union of admission inventories and all approved import-manifest inventories, with
the highest observed revision. Imports historically allowed additive allocations at
equal revision and did not update policy inventory. Replay preserves that history
and allocations known from manifest rows that were not imported; it never rewrites
historical events or persists a second inventory authority. Conflicting source or
legacy keys (including reverse project/task keys) cause journal integrity HOLD.
The same replacement validator runs live and during replay. A denied replacement
writes no event or operation key; exact completed-operation replay precedes new
replacement checks. This local preservation rule does not prove global inventory
completeness.

Dry-run input contains exact legacy snapshot text and digest, approved identity,
ownership evidence digest, ordered dependencies, completion policy/version and
optional completion reference. The deterministic manifest classifies rows as
UNBOUND, BOUND_CANDIDATE or QUARANTINED and lists a dependency-safe import order.
It cannot establish that the operator's declared global inventory is complete;
that declaration and administrative serialization require live qualification.
Missing ownership, unresolved dependencies and unqualified DONE evidence stay
staged. Duplicate IDs/keys and contradictory provenance are quarantined.

An approved import recomputes classification, validates the source mapping and
current policy, and checks its inventory against replay-derived known allocations
inside the transaction. A conflicting source or legacy allocation, including an
unimported reservation, returns `invalid_import_inventory` before any event,
operation key or checkpoint change. Exact completed-import replay precedes these
new-import checks. A valid import atomically preserves the legacy ID/status/links while advancing
the legacy lifecycle version once and setting binding version 1. It records the
snapshot as imported provenance, without fabricating earlier transition history.
Raw legacy metadata is not exposed in the ordinary task view. No actual legacy
corpus or ownership coverage is claimed by synthetic fixtures.

## Crash, delivery and restore boundaries

SQLite uses `BEGIN IMMEDIATE`, foreign keys and `synchronous=FULL`. A separate
append-only acknowledged-head checkpoint is fsynced after commit and before any
receipt or outbox event becomes visible. A failed checkpoint returns UNKNOWN and
holds the writer. Restart checks the journal chain, supported event schema,
projections, operation index and checkpoint. A missing/torn/mismatched checkpoint,
corrupt journal, older database or unknown schema holds operation replay.

An explicit approved reconciliation can advance an intact older checkpoint only
when the exact database head and acknowledged history are preserved. It adds a
reconciliation event, never reexecutes the earlier transition. Torn checkpoints
and missing acknowledged history require investigation; there is no auto-heal.
Missing, empty or zero-history anchors remain HOLD even when independent receipts
are supplied; reconstructing lost acknowledged history needs a separate protocol.
An intact nonempty acknowledged anchor permits DB-ahead recovery with no independent
receipts when the unacknowledged tail has no returned receipt.
Rolling back both the database and independent checkpoint cannot be detected from
those two files alone. Any restore must remain held and be reconciled against
preserved independent receipts. Unsupported schema upgrades require a separately
qualified isolated copy procedure; this release never migrates in place.

`drain_once` is explicitly invoked by the runtime and sends only checkpointed
events outside the SQL transaction. A failure holds later events for the same
project/task/destination. The trusted destination adapter must authenticate its
peer, validate the envelope and return a bound acknowledgment. Receivers must
dedupe `(project_id, event_id, destination)`. Hashes and `canonical_system` labels
are not authentication. Source fixtures exercise ordered retries and receiver
dedupe; real delivery credentials are absent. At-least-once delivery is the model,
not exactly-once external effects.

## Qualification and rollback

The focused tests cover strict contracts, temporary SQLite state, crash/replay,
authorization, isolated ASGI composition, kernel evidence and local maintenance.
They do not qualify deployed services, actual ownership inventories, credential
issuance/revocation, external receivers, fleet integration, storage growth or
performance. These remain NOT_RUN activation gates under a separate mandate.

Before activation, rollback means withdrawing only this isolated source delta
while retaining prior repairs and proof. After any accepted operation, disable
writes and preserve the database, checkpoint, journal and receipts. Forward-fix or
rebuild derived views under an approved maintenance packet. Never clear keys,
overwrite accepted history with a backup, or resume the old local writer.
