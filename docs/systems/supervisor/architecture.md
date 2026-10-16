---
id: supervisor-architecture
title: Local supervisor architecture
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-10-16'
last_review: '2026-10-16'
next_review: '2027-01-14'
prelude: Current single-host mechanisms and the boundary to proposed full-system supervision.
---
# Local supervisor architecture

The current candidate has two separate entrypoints. `dopemux.supervisor` runs trusted,
previously authorized deterministic v1 commands. `dopemux.governed_execution.admission`
checks explicitly synthetic owner fixtures. Neither entrypoint installs a live owner,
cloud bridge, provider adapter, daemon or canonical authority store.

## Current code and evidence

| Mechanism | Code | Focused evidence |
|---|---|---|
| Transactional mandate/grant/route/work/outbox admission | `Runtime._admit`, `Supervisor.admission_transaction` | `AtomicAdmissionTests` fault injection at five stages |
| Existing owner identity and canonical GEC validation | `OwnerAdmitter.admit`, `resolve_bound_identity` | `OwnerAdmissionTests` forged/stale/revoked/widened scope |
| Explicit synthetic owner port | `LocalOwnerResolver.resolve` | fixture CLI returns `execution_authorized: false` |
| One writer and shared/heavy exclusions in one journal | `Supervisor.claim_ready`, `_resources` | inherited kernel custody/parallel tests |
| Current narrowing during execution | `Supervisor.control_mandate`, `_gate` | second-process CLI denial and disjoint-project tests |
| Private immutable publication and local receipt | `exclusive`, `LocalDeliveryRecorder`, `ReturnPublisher` | overlapping link/read and forged legacy ACK tests |
| Durable intent and no blind replay | `recover_interrupted`, `Runtime.run` | inherited restart/no-reexecution tests |

Sources: [kernel](../../../src/dopemux/supervisor/kernel.py),
[runtime](../../../src/dopemux/supervisor/runtime.py),
[admission](../../../src/dopemux/governed_execution/admission/owner_admission.py),
[new tests](../../../tests/unit/full_system_r2/),
[inherited tests](../../../tests/unit/supervisor/).

## Single project and portfolio

One project uses one immutable v1 mandate with implementation and validation children.
Its route binding is qualified by mandate and exact route content, including executable
and deadline. A newly preferred route does not invalidate an existing running binding.
Identical re-admission never replenishes attempts, repairs, active time or expiry.

A local portfolio admits disjoint physical project roots into one private SQLite journal.
The coordinator schedules ready work up to the two-slot parser ceiling, also constrained
by each grant and writer/resource exclusions. A historical incomplete admission produces
an affected-project hold. Transport I/O failure leaves returns pending while unrelated
work continues; a conflicting immutable return holds its own project. Separate journals
have no shared physical custody fence and must not claim overlapping outputs.

Database admission commits mandate rows, grants, routes, works and outbox events together.
It does not make filesystem snapshots, subprocess effects or file publication SQLite-atomic.
A private per-directory publication lock prevents readers seeing the temporary two-link
inode during create-only publication. This is cooperative single-host coordination.

## Trust and limits

The protected local UID is inside the trust boundary. Private owner fixtures, state and
return directories must be current-user owned, canonical and mode 0700; owner records and
publication locks are private ordinary files. Same-account hostile code can impersonate
that local owner. Arbitrary local commands retain the account and enclosing tool sandbox's
permissions. Visible-write monitoring is detection, with known hidden/cache/vendor blind
spots; it is not containment. Process cleanup, executable drift and slow snapshot accounting
remain later work.

Native authorities retain their ledgers. The unchanged GEC validator checks canonical
receipt shape/provenance; the existing MCP resolver checks registered project/workspace/
instance identity. The new admission adapter adds owner-port checks before that seam and
intersects identities, effects, resources, routes, time, funding, attempts and delegation.
It currently supports only canonical `dispatch_input_receipt.v1` / `ScopeAuthority` in
explicit fixtures. Missing real owner bindings fail closed. Recheck resolves current
owner data again; a cached projection is never an execution grant.

## Proposed full-system target

Portable v2 schemas describe future owner admissions, identity, subjects, mandates and
governance records. They do not enable v2 execution. Later stages must connect actual
owner ledgers, resource custody across journals, role-bound ACKs, canonical task dispatch,
runner capability qualification, evidence integrity and measured budgets. Codex, Claude,
Grok, AGY, Command Code and OpenCode require separately verified supported interfaces;
this candidate assumes no undocumented API for any of them.

Use [interfaces](interfaces.md), [migration](migration.md) and [runbook](runbook.md)
for precise current contracts. The [adoption record](../../04-explanation/architecture/full-system-r2/adoption.md)
binds this candidate's source and known review history.
