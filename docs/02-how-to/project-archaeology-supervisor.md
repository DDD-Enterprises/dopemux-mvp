---
id: project-archaeology-supervisor
title: Project Archaeology Supervisor
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-09-27'
last_review: '2026-09-27'
next_review: '2026-12-26'
prelude: Run explicitly released archaeology tasks with external state, qualified routes, and durable terminal receipts.
---

# Project Archaeology Supervisor

`python -m dopemux.archaeology_supervisor` provides `validate`, `init`, `status`,
`run`, and `probe`. This module manages campaign dispatch receipts only.
Control Tower remains supervisor. It does not write GitHub, ConPort,
Task Orchestrator, service state, or PM truth. Implementation packet
`TP-DMX-PROJECT-ARCHAEOLOGY-SUPERVISOR-001` does **not** release campaign execution.

Use a POSIX host and local filesystem with working `flock`, `fsync`, atomic
rename, and hard links. Network filesystems and Windows are unsupported.
Supply an external state root outside every Git checkout; no default root.
Use the installed package or set `PYTHONPATH=src` in this worktree.

## Release and runner boundary

Campaign ledger is an immutable release snapshot. A task with `release_id: null`
is held. A non-null ID records an explicit operator release; this module does
not authenticate Control Tower or verify signatures. Only trusted operators
may supply ledgers or access state. State hashes detect corruption and bind
snapshots; they are not signatures or protection against a malicious writer.

The runtime launches exact operator-supplied argv with `shell=False`. No model
selectors, provider quota APIs, provider SDK adapters, quota inference from
error text, or automatic fallback are invented. Operators must qualify exact
commands externally, including model identity, privacy, disabled tool effects,
no retries/fallback, and any designated capacity-failure exit codes. A declared
model or `VERIFIED` label alone is not independent provider evidence.

Runner commands remain trusted executable code. This module is **not** an OS
sandbox and cannot prevent a released command from changing files or reaching
services. Use separately qualified read-only runner isolation. Do not supply
commands granting repository, GitHub, ConPort, Task Orchestrator, or service
effects without separate release. Credentials belong in existing authentication
facilities, never argv or ledger fields. Runner inherits process environment;
environment values and runner stdout/stderr are never included in receipts.

Each runner executes in its attempt directory. `spec.json` records command,
task ID, attempt ID, and binding hashes. Environment fields
`DMX_ARCHAEOLOGY_TASK_ID` and `DMX_ARCHAEOLOGY_ATTEMPT_ID` identify work.
Task input/output handling belongs to the qualified runner command: include
explicit external input/output arguments in its argv. No prompt substitution
or shell expansion occurs. Runner stdout/stderr are discarded; write intended
research artifacts to explicitly released external output paths.

## Version 1 campaign contract

JSON rejects unknown fields, duplicate keys, coercions, cycles, missing
references, and duplicate IDs. IDs contain letters, digits, `_`, `.`, or `-`,
start with a letter/digit, and have at most 128 characters.

```json
{
  "version": 1,
  "id": "DMX-PROJECT-ARCHAEOLOGY-001",
  "max_parallel": 2,
  "tasks": [
    {
      "id": "survey",
      "release_id": null,
      "depends_on": [],
      "capabilities": ["repo-read"],
      "privacy": "internal",
      "allowed_routes": ["qualified-reader"],
      "preferred_routes": ["qualified-reader"],
      "independent_of": [],
      "premium_allowed": false
    }
  ]
}
```

`depends_on` requires successful terminal receipts for every referenced task.
Failed/unknown tasks do not unlock downstream work. `independent_of` must be
contained in `depends_on`: a qualified route must differ in **both** family
and runtime from every prior attempt of those tasks. Independence is based on
externally evidenced ledger identities, not names guessed by the scheduler.
Tasks schedule in stable ID order. Unreleased tasks never dispatch.

## Version 1 route contract

Top-level fields: `version: 1`, `campaign_id`, `routes`.
Every allowed route must exist. Each route has exactly these fields:

| Field | Contract |
| --- | --- |
| `id` | Unique route ID. |
| `argv` | Nonempty string array; first element absolute executable path. Repeated flags allowed. No secrets. |
| `model` | Explicit externally evidenced model identity, not an invented selector. |
| `family`, `runtime` | Independence identities; valid IDs. |
| `capabilities` | Unique strings; must cover every task requirement. |
| `privacy` | `public`, `internal`, or `restricted`; must meet task privacy. |
| `qualification` | `status`, `evidence_id`, `command_sha256`. |
| `capacity` | `used_percent`, `slots`, `observed_at`, `ttl_seconds`. |
| `pool` | Shared quota/concurrency pool ID; all routes sharing pool need identical capacity/reserve snapshots. |
| `premium` | Boolean; premium routes require task `premium_allowed: true`. |
| `reserve_slots` | Nonnegative integer; reserved for premium-allowed tasks. Cannot exceed known slots. |
| `capacity_exit_codes` | Unique explicit integers 1–255; code 0 always success. No guessed provider mappings. |

Qualification is `VERIFIED` with an evidence ID and a matching command hash,
or `UNKNOWN` with null evidence/hash. Compute command hash as SHA-256 of
UTF-8 JSON serialized with sorted keys, separators `(',', ':')`, no NaN,
and one trailing newline. `dopemux.archaeology_supervisor.digest(argv)` exposes
this exact operation. Command qualification must be re-established outside
this runtime whenever commands change.

Capacity percentages are **used** capacity. Slots represent operator-observed
concurrent admissions in this shared pool, before reservations held by this
supervisor. Outside usage must already be accounted for in the snapshot.
`observed_at` is Unix time; `ttl_seconds` is a positive observation lifetime.
Null percentage or slots, stale observations, and future observations block
admission. `UNKNOWN` never means unlimited. There is no quota API polling.

| Used percent | Band | Admission |
| --- | --- | --- |
| Below 70 | GREEN | Within slots/reserve limits. |
| 70 to below 85 | YELLOW | Within slots/reserve limits. |
| 85 to below 95 | RED | Within slots/reserve limits; ranked after GREEN/YELLOW. |
| 95 or above | CRITICAL | Blocked. |
| Null | UNKNOWN | Blocked. |

Apply capability, privacy, exact-command qualification, release allowlist,
independence, freshness, premium policy, and shared-pool limits **before**
ranking. Choose least scarce band, then preserve premium quota, then prefer
plan-included routes (`preferred_routes`), then lowest percentage, then stable
route ID. Pre-dispatch diversion changes selected route before any attempt
launch. It is not an inference retry. Every selection remains inside explicit
allowed routes. Missing qualified capacity yields no dispatch.

Initialization pins campaign and all route declarations. Only capacity fields
may refresh in later route ledgers; changing command, identity, pool, reserve,
qualification, or other route declarations blocks execution. Reordering routes
is harmless. Use a separately released campaign/state root for revised routes;
never migrate unresolved attempts to another root to force redispatch.

## CLI sequence

Examples below illustrate commands; they do not grant release authority.
Use independently prepared campaign and route files outside the repository.

```bash
python -m dopemux.archaeology_supervisor validate \
  --campaign /external/campaign.json --routes /external/routes.json
python -m dopemux.archaeology_supervisor init \
  --campaign /external/campaign.json --routes /external/routes.json \
  --state-root /external/campaign-state
python -m dopemux.archaeology_supervisor status \
  --state-root /external/campaign-state
python -m dopemux.archaeology_supervisor run \
  --state-root /external/campaign-state --routes /external/routes.json --once
```

`run` defaults to one dispatch. `--max-dispatch N` permits a finite positive
number of dispatches per invocation; `--once` conflicts with values other than
one. Global `max_parallel` and shared-pool limits still apply. No polling daemon
or implicit retry loop runs. Call `status` to inspect detached receipts, then
explicitly invoke `run` again to schedule newly ready tasks.

`validate` writes nothing. `status` replays events and overlays independently
written receipts without changing event/checkpoint bytes. `run` incorporates
validated terminal receipts into events and rebuilds checkpoint before scheduling.
`ready` means dependency-ready, not capacity-qualified. An empty `dispatched`
array means nothing launched; it is not campaign completion evidence.

Metadata probes use only fixed executable/version commands, or OpenCode's model
catalog command (`opencode models`), with a finite timeout. They return a
sanitized version or catalog line count, never raw tool output. They do not
qualify models, authentication, quota, privacy, reasoning settings, or exact
inference capability. Missing executable returns `NOT_INSTALLED`; timeout
returns `UNKNOWN`. OpenCode catalog is metadata-only, not inference.

```bash
python -m dopemux.archaeology_supervisor probe claude
python -m dopemux.archaeology_supervisor probe opencode --catalog
```

## Crash, replay, and successor rules

One supervisor writer holds an exclusive nonblocking lock. It writes an
exclusive attempt spec, appends and fsyncs `INTENT`, replaces/fsyncs checkpoint,
then starts a detached wrapper. Intent reserves campaign and pool slots.
Wrapper waits for supervisor lock release to validate intent, durably marks
itself started, launches runner once, and writes an exclusive atomic terminal
receipt. It survives normal supervisor exit; it cannot survive host loss or
termination of the wrapper itself. No PID liveness inference releases slots.

Events form a sequenced hash chain. Replay validates chain and immutable
campaign/route binding. Checkpoint is derived and may be replaced even if
missing/corrupt. Terminal receipts are bound to immutable dispatch spec.
Malformed/mismatched/changed terminal receipts block scheduling.

| Outcome | Behavior |
| --- | --- |
| `SUCCEEDED` | Unlocks dependencies; never reruns task. |
| `CAPACITY_FAILED` | Original attempt stays failed; explicit successor release required. |
| `FAILED` or `LAUNCH_FAILED` | Terminal; no automatic retry or successor through this interface. |
| `OUTCOME_UNKNOWN` | Intent without receipt, including launch ambiguity; reserves slots and blocks duplicate dispatch. |

An explicit successor command is allowed only for the latest terminal
`CAPACITY_FAILED` attempt. Release ID must be distinct from existing attempts,
and invocation may dispatch at most once. Route still passes every hard filter.
Original receipt/event remains unchanged; successor has a new attempt ID.
Duplicate successor commands block after the first intent.

```bash
python -m dopemux.archaeology_supervisor run \
  --state-root /external/campaign-state --routes /external/routes.json \
  --successor-of attempt-000001 --successor-release operator-successor-002
```

A surviving wrapper receipt can reconcile `OUTCOME_UNKNOWN` to terminal status.
Missing receipt has no automatic recovery path. Operator must establish exact
outcome externally under a separately authorized recovery procedure; never
fabricate a receipt or delete an intent. Partial event lines, partial init,
or an orphan attempt directory fail closed and require operator recovery.
No log truncation, lease expiry, hidden retry, or state-root fallback occurs.

## Validation and rollback

Focused tests use synthetic Python runners only. They exercise scheduling,
route filters, capacity/reserves, shared pools, drift, durable launch ordering,
receipt custody, checkpoint recovery, lock exclusion, explicit successors,
literal argv, and receipt survival after supervisor process exits. No live
campaign, provider inference, or service integration is covered by those tests.

Rollback repository changes through a reviewed revert. Preserve external state
and receipts; reverting code must not erase evidence or authorize redispatch.
This packet adds no service startup, migration, or default CLI fleet wiring.
