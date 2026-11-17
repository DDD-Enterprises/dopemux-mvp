# MACRO-DMX-DESK-GATE-001-R1 — Issuance Record (reissue for base drift)

**Issued**: 2026-11-15 by the supervisor session (Claude Code desktop; configured model `claude-fable-5-2`, effort `medium` from `$CLAUDE_EFFORT`; observed model UNKNOWN).
**Supersedes**: `task-packets/MACRO-DMX-DESK-GATE-001/` (kept unchanged; see its `SUPERSEDED.md`). Read that folder's `ISSUANCE.md` for the workstreams, TP_ROUTE blocks, decisions D1–D4, design facts and open items. They apply here unchanged except as listed below.
**Authority**: NONE. This record and the package grant no execution authority.

## Why reissued

Execution of `MACRO-DMX-DESK-GATE-001` stopped at its first step. After `git fetch origin main`, `origin/main` was `365f70ce2edc907d14356d82d2843104dbdaa434`, 78 commits past the pinned base `589bb05`, and the drift changed two W02 files (`src/dopemux/claude/native_hooks.py`, `tests/test_native_hooks_workflow.py`). The child packets pin the base by SHA, so a new package was required.

## What changed from the superseded package

| Field | Change |
|---|---|
| `macro_id`, child `series`/`macro_id` | `MACRO-DMX-DESK-GATE-001-R1` |
| Base in each `rollback_boundary` | `365f70ce2edc907d14356d82d2843104dbdaa434` |
| `authority.operator_refs`, binding `operator_gate_refs` | the two operator instructions below added |
| Operator-gate stop condition | reworded to point at the recorded instructions |
| Binding `recorded_at` | reissue time |

Nothing else differs: objectives, write allowlists, invariants I01–I08, steps, routes, lane and audit requirement are byte-for-byte the same text.

## Execution gate

Recorded as given, in the operator's words (chat, 2026-11-15):

1. `AUTHORIZE_MACRO_DMX_DESK_GATE_001_EXECUTION=YES` (typed for the superseded package).
2. "Reissue and execute", in answer to "Reissue the macro pinned to the new origin/main (365f70c) and then execute it?"

The supervisor treats (1) plus (2) as the gate for this reissue because the base pin is the only change. No new phrase was typed for the `-R1` id.

## Package members

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `e6673bba32d91bf47fc581e9bbd0a50d21b8355602c312e2851b573585544a95` |
| `EXECUTION_BINDING.json` (coordinator) | `5fc6a01df99781a26e96e1f1a8bb77dab1cfbdb24f545b3c79b6999c8d67755d` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `aa2377e0ce94484034d6ab282882d850d610c5695215cdb08669340938c13686` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `21a08387be3482f3de5f53d39808644ffdf1a13e9a15ef2d0c6cd8b9167cdf7c` |

## Validation at reissue

| Check | Exit | Result |
|---|---|---|
| `ct validate-macro --file …/MACRO_PACKET.json` | 0 | PASS — `STATIC_VALID`, 0 errors, authority NONE |
| `ct validate-binding --file …/EXECUTION_BINDING.json` | 0 | PASS |
| DCP route / Task Orchestrator state | | NOT_RUN |

## Facts re-checked at the new base

- `native_hooks.py:367` dispatches `SessionStart` (was line 353).
- `.claude/settings.json` and `.codex/hooks.json` both still register `SessionStart`.
- The two W01 files still do not exist.
- New since the old base: commit `a274a066f` makes native hooks dispatch in linked worktrees and honour the payload `cwd`. W01's project-key rule (main checkout name, not worktree name) is unchanged by this, and W02-S1 must read the new code before choosing the call site.
