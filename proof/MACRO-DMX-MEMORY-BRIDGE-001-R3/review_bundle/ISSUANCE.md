# MACRO-DMX-MEMORY-BRIDGE-001-R3 — Issuance Record (repair of audit findings N1, N2, N5)

**Issued**: 2026-10-30 by the Control Tower supervisor session (Claude Code desktop, `claude-sonnet-5-5`, effort `high`).
**Operator instruction**: "Repair and re-audit" (2026-10-30, answering the question after the R2 audit).
**State at issuance**: PR #1483 is an open draft at `bff3fd46e` (operator-accepted PASS_WITH_RISKS at audited content head `52855fb35`; CI `independent embedded audit` and `PR Steward / final readiness` are red, as expected for an unsigned proof). `origin/main` is still `93050d135`. Authority: NONE.
**R2 is preserved unchanged.** The operator's acceptance and `FOLLOWUPS.md` stay as they are; R3 produces a new audited subject and a new verdict beside them.

## Execution gate

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R3_EXECUTION=YES
```

The final audit is a second gate (a new subject needs a new audit, and the first approval was for one attempt). Send this line as well, or name another route:

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R3_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT
```

Without the route line I repair, gate and freeze, then stop before the audit.

## Package members (the macro pins each by SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `f4d74cbf7679caf1c90e5f84b538b37b1a960734bb7a09f1801d60039c7572a0` |
| `EXECUTION_BINDING.json` (coordinator) | `b8b353e5fce5578dd2b2068a3ebc7568f70de4179f1a218e13e1c8fede8d9184` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `4421bac25fd84df7d68bd781633b4bc8c89df830bf52d25552e32f584336aa37` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `7ae73aaa28707edcd861bde8b6e794aa5f7bd36ad7b3385068dfb9794d75ab12` |

This file is not referenced by the macro and is not part of the pinned subject.

## Scope (sized to "docs and one string")

| WS | Finding | Change | Write allowlist | Route |
|---|---|---|---|---|
| W01 | N2 (MEDIUM) | `/bridge-note` description `Store a note in the capture ledger` → `Queue a note for the capture ledger`, in `register.tsx:1208` and its test assertion (`register.test.ts:1337`); 1 line each | `plugins/dopemux-memory-bridge/hooks/register.tsx`, `.../register.test.ts` | claude-haiku-5-5 → claude-sonnet-5-5 only on an evidence-backed STOP |
| W02 | N1 (MEDIUM), N5 (LOW) | drop the pinned commit hash `1ce149a76` and the test count from the how-to (lines 19, 137-138); reword README line 43 so `attempts` counts attempts that ran, including the final successful one | `plugins/dopemux-memory-bridge/README.md`, `docs/02-how-to/memory-bridge.md` | claude-haiku-5-5 → claude-sonnet-5-5 only on an evidence-backed STOP |

Not in scope (stay accepted follow-ups): N3 (other sessions' rows counted as pending), N4 (unbounded answer text before the decision regex), N6 (dead branch in the `/clear` fold), N7 (live run). N3, N4 and N6 would be code changes beyond a string; say so if you want them in.

W01 (code) and W02 (docs) have disjoint write surfaces and run in parallel (`max_mutating_workstreams` = 2); `ct validate-macro` accepts that. Effort is `UNKNOWN` for children (not settable from this runner).

```
TP_ROUTE   (coordinator)
runner=claude-code-desktop
model=claude-sonnet-5-5
effort=high
skills=task-packet
why=session pin; issuing a two-workstream repair macro

TP_ROUTE   (W01, W02)
runner=claude-code-agent
model=claude-haiku-5-5   (fallback claude-sonnet-5-5 on an evidence-backed STOP only)
effort=UNKNOWN
skills=NONE
why=one-line string change plus doc-line edits, each fully specified; cheapest adequate; cost UNKNOWN
```

## PROPOSED allowances (accepted by authorizing R3)

| Scope | Elapsed | Subagent tokens | Tool uses | Attempts |
|---|---|---|---|---|
| W01 | 20 min | 200,000 | 60 | 1 Haiku + 1 Sonnet fallback |
| W02 | 20 min | 200,000 | 60 | 1 Haiku + 1 Sonnet fallback |
| **Macro** | 2 h to a frozen head | 500,000 | — | 4 dispatches; 1 team-lead correction round |

Basis: the R2 docs child (Haiku) used 164,222 tokens, 17 tool uses and 101 s for a 149-line how-to; R3 edits are smaller. Active (model-working) time is not recordable by the harness. Intermediate audits 0; `advisor` 0 for every child and the coordinator. On a cap: stop, keep the uncommitted diff, return NEEDS_SUPERVISOR with the counters. `ct validate-macro` does not check these numbers; the team lead does.
Audit (outside the budget): 1 audit, 1 attempt, 0 retries, no fallback; the R2 run cost about $0.077 and 180 s.

## Validation at issuance

| Check | Result |
|---|---|
| `ct validate-macro` | PASS, STATIC_VALID |
| `ct bind-record` + `ct validate-binding` (coordinator) | PASS |
| `task_packet.v2` schema W01, W02 | PASS ×2 |
| Macro pins (2 task packets + binding) | MATCH |
| Child bindings, DCP route, Task Orchestrator state | NOT_RUN (child bindings are created per child at dispatch) |

## What happens to the PR

R3 adds commits after `bff3fd46e` and changes the audited subject. Nothing is pushed by me. After a passing re-audit you would need to re-attest and re-sign at the new head and push yourself; the open draft #1483 then carries the repaired head. The earlier acceptance stays on record for `52855fb35`.

## Execution outline (after the gate)

1. Preflight: head is `bff3fd46e` (or a descendant differing only under `proof/`), `origin/main` still `93050d135`, clean tree apart from the other sessions' `.codex/config.toml` and `.agents/`. Flatten this package into `proof/MACRO-DMX-MEMORY-BRIDGE-001-R3/review_bundle/` and commit it (proof-only).
2. `ct bind-record` + `ct validate-binding` per child, then dispatch W01 and W02 in parallel on Haiku; children never commit or call `advisor`.
3. The team lead re-reads both diffs (W01: exactly 1/1 line per file; W02: no hash or PR number left in the docs), parses transcripts, runs `claude plugin validate/test`, `tsc -p`, the docs gates and the change-contract preflight itself, commits W01 and W02 with explicit pathspecs, and freezes.
4. With the route line: the tool-less Grok recipe, probe first, one attempt, custody committed before the verdict is read, adjudication, then a new unsigned `PROOF.json` for the repaired head. No push, signing or merge.
