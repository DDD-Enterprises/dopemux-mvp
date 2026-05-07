# Safe Action Gate Specification

**Packet:** TP-DMX-COCKPIT-IA-RECONCILE-001
**Status:** NORMALIZED CANONICAL OUTPUT
**Supersedes (as canonical name):** `SAFE_ACTION_GATES.md`

The Safe Action Gate is the cross-cutting confirmation, proof, and governance contract interposed between any non-read action and its execution. Every action that is not `DISPLAY_ONLY` or pure `INSPECT_ACTION` must pass through this gate. The gate is **not** a destination surface; the operator is never asked to "open the gate" as a goal. It is invoked from PM, Implementer, Services, Events, the Command Palette, or Settings/Admin/Runtime when an action is requested.

## 1. Confirmation Tiers

The gate maps every action into exactly one tier. The tier determines what the gate must collect, prove, and log.

| Tier | Class | Required confirmation | Required preflight | Required post-action proof | Rollback / abort |
| --- | --- | --- | --- | --- | --- |
| T0 | `DISPLAY_ONLY` | None. | None. | Source authority and timestamp captured at view time. | n/a |
| T0i | `INSPECT_ACTION` | Explicit invoke; no defaults-on inspection with side effects. | Command preview. | Command path + exit/result summary + source authority. | n/a |
| T1 | `CONFIRM_REQUIRED` (generated artifact) | Confirm output path and overwrite behavior. | Preflight summary including output path, writer, expected artifacts. | Artifact path + checksum or summary; logged to evidence. | Abort allowed before write; rollback if writer supports. |
| T2 | `CONFIRM_REQUIRED` (config mutation) | Confirm target file/service and before/after diff. | Effective-config preview with diff or `UNKNOWN` flag if diff is not derivable. | Config diff or post-action status; logged. | Rollback path explicit or block. |
| T3 | `CONFIRM_REQUIRED` (write local) | Confirm path and side effect; show classification. | Preflight summary with path and side-effect class. | Filesystem diff, artifact path, or exit code. | Block if rollback path absent for destructive writes. |
| T4 | `CONFIRM_REQUIRED` (write remote) | Confirm remote target, account/context, idempotency. | Effective remote target preview. | Remote receipt or API result captured. | Block by default until remote-mutation policy approves. |
| T5 | `CONFIRM_REQUIRED` (start/stop service) | Confirm service, scope, and expected state transition. | Pre-state snapshot. | Post-action status/log evidence + exit code. | Abort allowed before transition; revert path explicit. |
| T6 | `CONFIRM_REQUIRED` (execution handoff) | Confirm TP/task id, runner, cwd, branch, output/proof target. | TP gate must be present; preflight summary required. | Exit code + proof path + validation summary. | Abort allowed before runner starts; in-flight cancellation routed through runner authority. |
| TX | `BLOCKED_IN_COCKPIT` | None executable. | n/a | Block reason + replacement command (if any) + required external workflow recorded as evidence. | n/a |
| TU | `UNKNOWN` | None executable. | n/a | Investigation packet reference recorded as evidence. | n/a |

## 2. Required Inputs To The Gate

For every invocation that is not T0 or TX/TU, the gate must collect and display these fields **before** the operator is offered a confirm affordance. If any required field cannot be resolved, the gate fails closed.

- `command` — fully resolved invocation including subcommands.
- `target` — file, service, remote endpoint, or task id targeted by the action.
- `worktree` / `cwd` — resolved against the current worktree (this packet's worktree, never `/tmp` as authoritative).
- `authority_domain` — owning domain from the inventory.
- `canonical_writer` — system or service that owns the write; if shared, every writer must be listed.
- `side_effects` — enumerated side effects from the safety class plus per-row notes.
- `proof_artifact` — expected proof artifact path or evidence stream key.
- `rollback_or_abort` — explicit rollback path, abort token, or `NOT_APPLICABLE` with a reason.

## 3. Post-Action Proof Expectations

After execution, the gate must record proof appropriate to the tier. Missing proof escalates the row into the Unknown/Drift Queue with an explicit "stale proof gate" tag.

| Tier | Proof captured |
| --- | --- |
| T0 / T0i | Inspect result + source authority + timestamp. |
| T1 | Artifact path, checksum/summary, exit code if invoked through a runner. |
| T2 | Config diff, before/after status, command exit code. |
| T3 | Filesystem path, action verb, result, exit code. |
| T4 | Remote receipt (id, endpoint, actor, status), captured response body excerpt where governance allows. |
| T5 | Service before/after status, log excerpt, exit code. |
| T6 | TP id, runner id, cwd, branch, exit code, proof path, validation summary. |
| TX | Block reason, replacement command (if any), evidence of attempted selection. |
| TU | Reason unknown, required investigation packet id. |

## 4. Failure And Drift Handling

- Confirmation timed out or operator aborted: log abort, no execution, no proof; re-route to Palette if needed.
- Preflight could not resolve required input: fail closed, escalate to Unknown/Drift Queue with the missing-field reason.
- Proof missing after execution succeeded: mark row as `STALE_PROOF` in Unknown/Drift Queue and surface in Overview drift summary.
- Action class disagrees with carried-forward classification: block until reclassified through a packet (cannot be reclassified inside the gate).

## 5. UI Requirements

- The gate must show the safety tier badge.
- The gate must show every required input. Missing inputs must render `UNKNOWN`, not blank.
- The confirm affordance must require an explicit action (button click + optional typed confirmation for T4/T6/TX-adjacent tiers).
- The gate must never auto-confirm based on prior selection.
- The gate must never replace a blocked row with a confirmable one.

## 6. Source Artifact

`SAFE_ACTION_GATES.md` carried into this packet defined the original gate table. This spec normalizes it under the required name and adds explicit confirmation tiers, post-action proof expectations, and drift behavior. The gate definitions remain consistent with `COMMAND_EXPOSURE_POLICY.md` / `.json`.
