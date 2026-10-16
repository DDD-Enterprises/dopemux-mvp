---
id: supervisor-runbook
title: Operate trusted local supervisor fixtures
type: runbook
owner: '@hu3mann'
author: Codex
date: '2026-10-16'
last_review: '2026-10-16'
next_review: '2027-01-14'
prelude: Inspect local status, narrow live work and retain unknown effects conservatively.
---
# Operate trusted local supervisor fixtures

This runbook covers single-host trusted local commands and explicit synthetic owner
fixtures. It does not qualify production execution or hostile child code. Use installed
Python and the approved enclosing sandbox. No provider keys or network service are needed.

## Start and inspect

Follow the [quickstart](../../02-how-to/local-project-supervisor.md) with canonical project
paths and private state/return roots outside every project. Record exact argv, source,
issuer evidence, T0 and unchanged allowances before admission. `status` opens local metadata
but launches no work; `run` is explicit. Run exits 0 for completion pending native acceptance,
3 for held work, 4 for unfinished/blocked work, 2 for malformed input/local I/O failure.

During a run, a second same-account process can narrow an admitted mandate:

```sh
python3 -B -m dopemux.supervisor --state-root /approved/private/state   --return-root /approved/private/returns --receiver-ref local-operator   control mandate-id --sequence 1 --receipt-ref local-owner-denial   --action deny --gate security
```

Replace illustrative paths and IDs with approved ones. Sequence is increasing per mandate;
receipt identity is immutable. Use `--action revoke` or a declared `--action stop --condition`
when appropriate. Controls acquire only a short SQLite transaction. They never grant a PASS,
release a hold, extend a clock or create an upstream owner receipt. Polling cancellation is
cooperative; inspect native process evidence and retained unknown custody.

## Return delivery

`receive` explicitly writes local delivery records; `deliver` retries pending outbox events.
Both are safe to repeat for identical key/digest. A local receiver label is not authenticated
Native or Master identity. Temporary delivery I/O leaves events pending and does not halt
unrelated project execution. A conflicting immutable record holds its own project; preserve
both offending bytes and journal references for owner disposition. Do not overwrite it.

The local publisher coordinates readers across its fsynced create-only publication window.
Private same-UID directories are required; no directory permission repair is automatic.
The queue retains files and currently has no archive/rotation/backpressure protocol.

## Failure and recovery

Successful local subprocess completion now passes through a `Runtime.run` step-boundary
checkpoint before kernel finish. `state/evidence/<attempt>/STEP_BOUNDARY_CHECKPOINT.json`
binds the actual running dispatch/fingerprint and SHA-256/length identities of stdout,
stderr, native process result and start ACK. The create-only fsynced artifact and journal
`CHECKPOINT` are separate persistence steps; an artifact alone cannot establish a finished
step. Failed/unconfirmed children do not create successful checkpoint evidence.

| Observation | Required action |
|---|---|
| Missing real owner port | hold that path; explicit synthetic fixture is not a fallback grant |
| Revoked/expired/stale owner or binding | preserve evidence, re-resolve current owner; do not reset allowance |
| Historical incomplete admission | affected-project hold; unrelated project may progress |
| Interrupted RUNNING / cancellation | EFFECT_UNKNOWN; retain output and heavy-resource custody |
| Child exited; interruption before checkpoint or before kernel finish | preserve native evidence and any checkpoint; recovery holds EFFECT_UNKNOWN, never promote or replay |
| Step finished; interruption before local delivery | retain completed attempt; receive/deliver identical returns without rerunning work |
| Missing/mismatched checkpoint evidence or immutable artifact conflict | hold unknown effects; preserve offending bytes and actual attempt, do not overwrite or retry |
| Changed monitored input/output view | hold; obtain trusted explicit reconciliation |
| Malformed/parser result | retain native stdout/stderr/exit and successful prior stages; no implicit work replay |
| New security/publishing/spend/human phase | return to actual upstream owner gate |

`reconcile` is a trusted evidence-recording interface, not a process-termination detector or
authenticated acceptance bridge. A process-closed flag alone is not proof. Settlement and
stop-release/rebaseline behavior have known deferred limitations; this runbook does not
certify them. Automatic checkpoints cover completed local step boundaries only; the kernel
API is not wired to mid-command local-runner checkpoints or checkpoint-based task resumption.
Harness repair is zero in the current local adapter. Ordinary repair/retest is allowed only
when already listed in the finite mandate.

## Focused verification

From a source checkout with installed pinned tools:

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests/unit/full_system_r2 -t tests/unit -v
PYTHONPATH=src python3 -B -m unittest discover -s tests/unit/supervisor -v
```

The full repository pytest entry additionally needs its actual conftest dependencies and
pytest-asyncio plugin under disabled autoload; do not install or silently substitute a runner
when that binding is unavailable. Bind complete commands and capture real stderr/exits/counts.
Fixtures exercise actual local subprocesses but prove no live provider, cloud ACK, OS sandbox,
canonical admission installation, cash metering or production readiness.
