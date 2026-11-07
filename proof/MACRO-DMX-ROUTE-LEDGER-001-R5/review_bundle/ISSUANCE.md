# MACRO-DMX-ROUTE-LEDGER-001-R5 — Issuance Record (repair of the R4 findings)

**Issued**: 2026-10-30 by the Control Tower supervisor session for this worktree (Claude Code desktop, `claude-sonnet-5-5` per the session's system prompt; observed identity needs a runtime receipt), started by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c`.
**Status**: ISSUED, NOT EXECUTED. Authority NONE. Nothing in R5 was run, changed, committed, pushed or signed. The package is untracked under `task-packets/`. R1 to R4 are preserved unchanged (R4: 12 of 12 hashes re-verified).

## What the operator asked for

After the R4 report the operator chose **"Repair findings first"**, then selected **all four groups** (`N11, N12, N13a`; `N8 + docs O1-O5`; `N2, N3, N4`; `N5, N9 (design)`) and **"Both routes again"** for re-verification. Every repair changes the audited subject, so the R4 audits and the unsigned R4 proof no longer cover the repaired code; they stay untouched as history.

## Why two macros, and why this one is a repair macro

The re-audit must be pinned to the repaired head, which does not exist yet. So R5 **repairs, verifies and commits**; a **separate audit macro (R6)** is issued afterwards, pinned to the repaired head (merging `main` first if it moved), with its own operator line. R5 runs no auditor and spends no audit allowance. The earlier repair "all 3" was made on a direct instruction without a packet; this one, ten interacting repairs, gets a packet.

## The repair design (W01 implements it test first; the full text is in W01's invariants D1-D10)

| Item | Finding | What changes | Design choice worth your confirmation |
|---|---|---|---|
| D1 | N11 | the last main-loop step is kept in a ledger field, so the `/route-ledger` main row works with receipts off | none |
| D2 | N12 | empty-string effort and empty advisor id are rejected; `toBindingFields` maps empty to UNKNOWN | none |
| D3 | N13a | toast-once keys are rebuilt from the receipts on a hot reload, so no repeat toast | none |
| D4 | N4 | `session.end` makes ONE more awaited flush if a segment is still dirty | one retry, never more |
| D5 | N8 | `STATUS_DEBOUNCE_MS` is exported and the test advances `STATUS_DEBOUNCE_MS - 1` then 1 ms | none |
| D6 | N2 | `$.fs.stat(path, { resolve: true })` (it exists in this build, I had assumed otherwise): trailing slash on the default counts as the default; a symlinked or non-directory receipt dir disables receipts; a RELATIVE dir must resolve inside the project root; a symlinked segment file is never written; absolute explicit dirs stay allowed by design | **policy**: refuse symlinks, keep absolute dirs allowed |
| D7 | N3 | closed, clean segments with no unjoined agent_request are evicted from memory after a flush; per-kind counts, the last main step and `s.agents` stay; rehydrate evicts as it reads | **rule**: never evict a dirty or still-unjoined segment, so spawn-join mutation stays safe |
| D8 | N5 | after `/clear` the ledger re-initialises and the next hook re-resolves `$.session.id()`: a new id means a new file and fresh counts, an unchanged id continues the same file | **UNKNOWN** whether the host changes the id on /clear; both cases are handled and tested |
| D9 | N9 | new option `recordDescription` (boolean, **default false**): the Agent description is not recorded and the unpinned toast names the subagent type and short tool id instead | **default changed to omit**; opt in to restore today's behaviour |
| D10 | O1-O5 | README and how-to describe the 3.5 MB rollover, the 120-character stem, symlink handling, /clear, the new option, eviction and the main row; "five" comment fixed; `last_review` set to today; missing tests added (byte rollover via a minimal documented seam, unreadable segment and corrupt line, the command catch) | none |

Not in R5: **N1** (the live session; yours to run) and **N10** (API drift and plugin coexistence; not code defects).

## Workstreams and TP_ROUTE

| WS | What | TP_ROUTE (runner, model, effort) | Fallback |
|---|---|---|---|
| W01 | implement D1-D10 test first in six files (`register.tsx`, `register.test.ts`, `README.md`, `plugin.json`, `receipt.schema.json` comments only, the how-to); no commit | `claude-code-agent`, `claude-sonnet-5-5`, `high` | none |
| W02 | structural transcript check, whole-diff review against D1-D10 with file:line, every gate re-run independently, two commits (the repair; then the proof files); no auditor | `claude-code-desktop`, `claude-sonnet-5-5`, `high` | none |

Cost-first: one Sonnet child does the bounded implementation of an explicit design; the coordinator keeps verification and finality. `high` effort because eviction and session re-initialisation interact (lowest effort judged sufficient for correctness). The child may not commit, push, call `advisor`, run any model client, or touch anything outside the six files; the coordinator never edits a content file (a defect goes back to W01 as the one narrow repair dispatch).

Stops (any one halts the macro): a repair design proves unsound against the real API or needs a structural schema change; an existing test regresses without an enumerated legitimate change; any allowance; any write outside the allowlist; any advisor call by the child or a second by the coordinator.

## Proposed allowances (PROPOSED; none binds until you authorize R5)

Basis: estimates scaled from the measured R2 build (W01 core 14.6 min active, 69 tool calls, 217,502 to 433,391 tokens), because ten interacting repairs test first touch the same two large files.

| Allowance | W01 repair | W02 verify | Macro |
|---|---|---|---|
| Max active (child run time) | 75 min | n/a | 75 min |
| Max elapsed | 120 min | 60 min | 240 min |
| Dispatches (1 build + 1 narrow repair) | 2 | 0 | 2 |
| Automatic retries | 0 | 0 | 0 |
| Tool calls / tokens | 250 / 5,000,000 | n/a | 250 / 5,000,000 |
| Advisor calls | 0 | coordinator <= 1 | children 0, coordinator <= 1 |
| Final audits / intermediate audits / post-freeze repair rounds | — | — | 0 / 0 / 0 |

When a limit is reached or about to be exceeded: stop at the next safe point, leave the child's edits uncommitted, report `NEEDS_SUPERVISOR` with the allowance, the measured value, the cap and the files touched. At close `ALLOWANCE_LEDGER.json` records measured versus cap.

## Operator gate (execution starts only after you type this verbatim in chat)

```
AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R5_EXECUTION=YES
```

The R1 to R4 lines do not authorize R5.

## Open risks

| Risk | State |
|---|---|
| The repair adds surface | Eviction, session re-initialisation and the stat checks are new code on the hot paths of a mod that has still never run live on a repaired head; the next audit may raise new findings. This loop is not guaranteed to converge: I recommend this be the last repair pass before signing. |
| D8 premise | Whether the host changes the session id on `/clear` is UNKNOWN; both outcomes are specified and tested, but only a live session shows which happens. |
| D9 default | `recordDescription` defaults to false: receipts carry an empty `description`, which is a visible change for anything that reads it. |
| Child quality | A Sonnet child implements an explicit design; the coordinator's whole-diff review, independent gates and the later audit are the safeguards. Observed child model needs a transcript receipt. |
| Not run | A live session on the repaired head (N1), the `markdownlint` hook (Node env cannot install on this host), DCP and Task Orchestrator. |

## What you provide next

1. The R5 gate line above (and tell me before it if you want to change any bold design choice).
2. After R5 completes: a new audit macro (R6) pinned to the repaired head with its own gate lines for both routes; main is re-checked first.
3. Unchanged and yours: attest independence, sign, push, readiness, merge, and the N1 live check (do it on the repaired head, before or after the audit, but before relying on the mod).

## Package members

The macro pins the coordinator binding, each TASK_PACKET and (through `base_policy`) `ALLOWANCES.json`. Child bindings are listed for the record and are not pinned.

| Member | SHA-256 | Pinned by macro |
|---|---|---|
| `MACRO_PACKET.json` | `eb2f26ef8a0f502ac3c3a1f272acae7221800ac32650afac51a487a2061a1fb3` | n/a (the subject) |
| `EXECUTION_BINDING.json` (coordinator) | `d91c3519ab388d260dbc886a56990ddc0916695edf5f69e8bd6e0fd48e46cd33` | yes |
| `ALLOWANCES.json` | `15c7be8295d9503a263feccc58f50384a1851ad306d5c1c1261e4ec1738fb9f9` | yes (base_policy text) |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `8146cfdc8169b2ac587af0d4c98a941d252cecfbebcb214e83382dac2a5f748a` | yes |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `3f5ffe7707ce319bec1626bb959bd73b46a824c6e466642fb6659066b460dee0` | yes |
| `WORKSTREAMS/W01/EXECUTION_BINDING.json` | `84d55c6b6e33831ee19ed28cac9986d2de40c6d4889a3375d1b1ce5d637ebaef` | no |
| `WORKSTREAMS/W02/EXECUTION_BINDING.json` | `d8b6aca95ca3830e1ae1cc00868a4184f219425a970d46dc96dd071096b2b0ce` | no |

This file is not referenced by the macro and is not part of the pinned subject.

## Validation of this package

| Check | Result |
|---|---|
| `ct validate-macro` | PASS: `STATIC_VALID`, 0 errors |
| `task_packet.v2` schema (local registry), W01 and W02 | PASS x2 |
| `ct bind-record` then `ct validate-binding`, coordinator, W01, W02 | PASS x3 (authority NONE) |
| W01 text carries D1-D10 and the six-file allowlist | checked |
| R1 to R4 packages re-hashed | identical (R4: 12 of 12) |
| Any R5 workstream, edit, commit, auditor run | NOT_RUN |

The recorded bindings live in this worktree's gitignored `.control-tower/state/bindings/` only.

## Execution outline (after the gate)

1. Pin check (HEAD `0ca60b59b`, clean tracked tree, hashes, bindings); start an allowance log.
2. Dispatch W01 (Sonnet, `high`) with the packet path; it works test first and returns without committing.
3. W02: structural transcript parse, whole-diff review against D1-D10, every gate re-run, commit the repair, commit the proof files, STOP and report the repaired head.
4. Then, with your next gate line, the audit macro.
