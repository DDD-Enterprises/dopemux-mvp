# MACRO-DMX-ROUTE-LEDGER-001-R2 — Amended Issuance Record

**Amended**: 2026-10-23T20:23Z by the Control Tower supervisor session (Claude Code desktop, `claude-sonnet-5-5` per the session's system prompt, effort `high` per `$CLAUDE_EFFORT`), started by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c`.
**Why a revision**: the merge owner found that R1 recorded no numeric active or elapsed allowances, so a later accounting dead end was likely. R2 adds them, marked PROPOSED, and changes nothing else of substance.
**R1 is preserved unchanged** at `task-packets/MACRO-DMX-ROUTE-LEDGER-001/` (its nine files re-hashed after R2 was written: identical). The operator's verbatim R1 line, `AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_EXECUTION=YES`, covers R1 only; **R2 needs its own line** (below). No R1 child produced any output (see "What ran").
**Authority**: NONE. Nothing in R2 was executed, committed, pushed, signed or merged.

## Execution gate

Execution of R2 starts only after the operator types, verbatim, in chat:

```
AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R2_EXECUTION=YES
```

## What ran under R1 (so the accounting starts honest)

| Event | Result |
|---|---|
| Premature dispatch of W01 (a Sonnet child, effort high), on a relayed paraphrase of the gate | Stopped by the coordinator before it wrote anything. `git status` clean apart from the untracked package. |
| W01 dispatched again after the operator's verbatim R1 line | Stopped by the coordinator on the pause instruction while it was still reading the declaration. It wrote nothing: `git status --porcelain` showed only the untracked package, `git diff` empty, `plugins/dopemux-route-ledger/` absent. |
| W02, W03 | Never dispatched. |
| Commits | None. HEAD is still `93050d135ffc2592000c1d0edef82b2912935525` (equal to `origin/main`). |
| Active time, tokens and tool calls of the two stopped W01 runs | UNKNOWN: the stopped runs returned no totals. They are NOT counted against R2's allowances and are recorded here instead. |

## What changed from R1

- **New ids** so both validated records coexist in local binding state: macro `MACRO-DMX-ROUTE-LEDGER-001-R2`; children `TP-DMX-ROUTELEDGER-W01-CORE-001-R2`, `-W02-SURFACE-001-R2`, `-W03-DOCS-001-R2`; audit group `AGY-ROUTELEDGER-001-R2`.
- **Allowances** (`ALLOWANCES.json`, new member) plus invariant **I09** in every child, a global stop condition and a `base_policy` summary in the macro that pins `ALLOWANCES.json` by SHA-256.
- **Truthful placement**: R1 named branch `feat/route-ledger-001` and worktree `.worktrees/route-ledger-001`; the parent session told the coordinator to work in this worktree, so R2 names branch `claude/route-ledger-001-8d8032` and this worktree in the rollback boundaries and the custody constraint.
- The coordinator and child bindings carry the R2 operator reference and an `allowance exhausted` stop condition. Routes, write allowlists, workstream design, effort pins and the advisor ban are unchanged from R1.

## Package members

The macro pins the coordinator binding, each child TASK_PACKET and (through `base_policy`) `ALLOWANCES.json`. Child bindings are listed for the record and are not pinned (mutable local state, re-recorded per worktree).

| Member | SHA-256 | Pinned by macro |
|---|---|---|
| `MACRO_PACKET.json` | `f1591ee34c683d38f6c8ee91168acc04b7493b13ba15681ac32858459796ffa9` | n/a (the subject) |
| `EXECUTION_BINDING.json` (coordinator) | `a38b37d70c92b0dc61d8d1c627bc5b7e91361bcfd4132792eaf6d9a7e5b219d3` | yes |
| `ALLOWANCES.json` | `8731e0290fcfd6273ede0b1977bbb2a2d8b1fc13a223f867869a21e128c23cc7` | yes (base_policy text) |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `99bd1e68be39f8f8f35d4fb1f7f0e4c7b70b1b5addeaf7fdb92ca3cc5aa1355f` | yes |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `1e75decd96c0299d397b6785b246bdc968a385f6e2088fbeb8bf9b18d686c4a0` | yes |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `148099dad9ceb15f87bba17304e7669131d4e5a27aada25b45bbc142a38e83cc` | yes |
| `WORKSTREAMS/W01/EXECUTION_BINDING.json` | `366cd2038ca1dc7170dcc5157641dbcfb08ac2295bf578b145ce54cb9f118334` | no |
| `WORKSTREAMS/W02/EXECUTION_BINDING.json` | `2478872a4acaa8d775140294d38516e8d000f61d24ce2ee42f3130f09137f88f` | no |
| `WORKSTREAMS/W03/EXECUTION_BINDING.json` | `8709d252088a58c15cd85b775d75e5a6dd0505af4bbc69e4bc00e41288746131` | no |

This file is not referenced by the macro and is not part of the pinned subject.

## Proposed allowances (all PROPOSED; none binds until the operator authorizes R2)

**Basis: estimates.** No comparable macro recorded per-child active time or token totals. Pulse's commits span 2026-10-21 14:10 to 22:18 PDT, with operator waits and a session restart in between, so its elapsed time cannot calibrate these caps. The numbers are sized from the deliverable's scope and are meant to be revised after the first measured run, by an amended revision.

| Allowance | W01 core | W02 surface | W03 docs | Macro |
|---|---|---|---|---|
| Max active time (child's own run time) | 45 min | 30 min | 10 min | 85 min (sum) |
| Max elapsed (dispatch to return; macro: whole execution incl. gates, commits, freeze) | 75 min | 50 min | 25 min | 240 min |
| Max child dispatches (1 build + 1 narrow repair; W03's Sonnet fallback is the 2nd) | 2 | 2 | 2 | 6 |
| Max automatic retries (timeout, 429, route error is a STOP) | 0 | 0 | 0 | 0 |
| Max child tool calls (`totalToolUseCount`) | 150 | 100 | 40 | 290 |
| Max child total tokens (`totalTokens`; counting basis UNKNOWN, may include cache reads) | 3,000,000 | 1,500,000 | 400,000 | 4,900,000 |
| Max coordinator re-reads of a diff | 2 | 2 | 2 | — |
| Max advisor calls | 0 (child) | 0 (child) | 0 (child) | children 0; coordinator ≤ 1, at freeze only |
| Max intermediate model audits | — | — | — | 0 (schema constant) |
| Max final independent audits | — | — | — | 1 (operator-gated, not run by this macro) |
| Max post-freeze repair rounds without the operator | — | — | — | 0 |

**What can actually be recorded**: elapsed from the coordinator's clock at dispatch and return; active time, tool calls and tokens from the Agent result (`totalDurationMs`, `totalToolUseCount`, `totalTokens`); advisor calls by a structural count of the child's transcript. A figure the runner does not report is UNKNOWN and never counts as within budget. The coordinator's own tokens and active time are **not recordable** and are not budgeted.

**When a limit is hit**: stop the running child at the next safe point (TaskStop, never mid-commit), dispatch nothing further, retry nothing, substitute nothing, leave the child's edits uncommitted, and report `NEEDS_SUPERVISOR` with the allowance, the measured value, the cap and the files touched. A cap changes only by an amended revision with new hashes and a new operator line.

**Enforcement is coordinator discipline only.** Neither `macro_packet.v2` nor `execution_binding.v2` has a field for allowances (both are closed schemas) and `ct validate-macro` does not check them; whether any other tool does is UNKNOWN. Pinning is by the children's I09 text, the macro's stop-condition and `base_policy` text, and `ALLOWANCES.json`. I did not widen a schema. At close the coordinator writes `ALLOWANCE_LEDGER.json` (measured vs cap) into the flat `proof/MACRO-DMX-ROUTE-LEDGER-001-R2/review_bundle/`; it never invents a value.

## Workstreams and TP_ROUTE (unchanged from R1)

| WS | Write allowlist | Deps | TP_ROUTE (runner, model, effort) | Fallback |
|---|---|---|---|---|
| W01 ledger core, receipts, schema | `plugins/dopemux-route-ledger/` `.claude-plugin/plugin.json`, `hooks/hooks.json`, `hooks/register.tsx`, `hooks/register.test.ts`, `receipt.schema.json` | none | `claude-code-agent`, `claude-sonnet-5-5`, `high` | none |
| W02 status segment, `/route-ledger` (+`/route`), budget toasts, README | `plugins/dopemux-route-ledger/` `hooks/register.tsx`, `hooks/register.test.ts`, `README.md` | W01 | `claude-code-agent`, `claude-sonnet-5-5`, `medium` | none |
| W03 how-to | `docs/02-how-to/route-ledger.md` | W02 | `claude-code-agent`, `claude-haiku-5-5`, `low` | `claude-sonnet-5-5`/`medium`, only after an evidence-backed STOP |
| Coordinator | none (commits by explicit pathspec) | — | `claude-code-desktop`, `claude-sonnet-5-5`, `high` | none |
| Final audit | none | W01-W03 | operator-gated, NOT_RUN; different family from Claude | n/a |

`model_observed` is UNKNOWN for every child until a runtime receipt shows it. Children never call `advisor` (I03).

## Validation of this revision

| Check | Result |
|---|---|
| `ct validate-macro --file MACRO_PACKET.json` (R2) | PASS: `STATIC_VALID`, 0 errors |
| `ct bind-record` then `ct validate-binding` on the emitted path, coordinator `MACRO-DMX-ROUTE-LEDGER-001-R2` | PASS |
| Same, `TP-DMX-ROUTELEDGER-W01-CORE-001-R2`, `-W02-SURFACE-001-R2`, `-W03-DOCS-001-R2` | PASS ×3 |
| `task_packet.v2` schema (jsonschema), W01-W03 | PASS ×3 |
| R1 package re-hashed after R2 was written | identical (preserved) |
| DCP route, Task Orchestrator state | NOT_RUN (unchanged from R1) |

All R1 facts, decisions and open items in `../MACRO-DMX-ROUTE-LEDGER-001/ISSUANCE.md` still stand (declaration version skew, receipts layout, `/route-ledger` canonical with `/route` alias, no deny mode, Pulse status coexistence UNKNOWN, no live proof, audit route operator-gated, flatten the package into `proof/…/review_bundle/` before any PR and copy every audit artifact in immediately). The recorded bindings live in this worktree's gitignored `.control-tower/state/bindings/` only; an executing worktree must record and validate them again.

## Execution outline (after the R2 gate)

1. Re-check `HEAD` against a freshly fetched `origin/main` and the package against these hashes; record each child's dispatch and return times.
2. Dispatch W01 (Sonnet, `high`) with the packet path, the declaration and reference paths; schedule a wake-up at its elapsed cap. Re-read its diff, parse the transcript for `advisor_calls`, run its gates, commit it by explicit pathspec at once. Then W02 (Sonnet, `medium`), then W03 (Haiku, `low`), each committed before the next dispatch.
3. Run `claude plugin validate/test`, `tsc -p` if types are laid, the schema check, the docs hooks, the change-contract preflight and the pre-commit range; freeze (J02) at a gate-green head and stop. The final independent audit is operator-gated and not run by this macro.
4. Return one aggregate (authority NONE) with the frozen head SHA, per-child requested vs observed model, the gate table, `ALLOWANCE_LEDGER.json`, remaining uncertainty and the audit-route decision.
