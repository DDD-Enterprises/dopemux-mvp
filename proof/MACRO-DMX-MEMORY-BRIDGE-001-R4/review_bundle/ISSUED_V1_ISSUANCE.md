# MACRO-DMX-MEMORY-BRIDGE-001-R4 — Issuance Record (repair of re-audit findings N3, N4, N6)

**Issued**: 2026-10-30 by the Control Tower supervisor session (Claude Code desktop, `claude-sonnet-5-5`, effort `high`).
**Operator instruction**: "Repair N3, N4, N6" (2026-10-30, answering the question after the R3 re-audit).
**State at issuance**: branch head `afa4390bc` (R3 closure, unsigned `PROOF.json`); the R3 re-audit (Grok `PASS_WITH_RISKS`, Q1-Q13 PASS) audited content head `c71e7c1f4`. PR #1483 is a draft at `bff3fd46e`. `origin/main` is `93050d135`. Authority: NONE. R2 and R3 records stay unchanged.

## Execution gate

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R4_EXECUTION=YES
```

R4 changes the audited subject again, so a third audit needs its own route line (the earlier approvals were one attempt each):

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R4_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT
```

Without the route line I repair, gate and freeze, then stop before the audit.

## Package members (the macro pins each by SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `73a4d94b9fcac84459fd784f7cf732ba273c99350d83b0386c392f00852186e2` |
| `EXECUTION_BINDING.json` (coordinator) | `5311efc04375a5f5dc927b490a6f9858c3e1cef742a32e866f1551318c8c2889` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `5b2ad0c47f52385379cb7bae2a072cdd3717c0c23ce7375626fbe4c181fac7ae` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `c97aafe57cd2bec48472923f5d0f3429659b25b5ff75fbee04bf11ff366f15ce` |

This file is not referenced by the macro and is not part of the pinned subject.

## What changes

These are code changes beyond a string, so W01 runs on Sonnet and W02 (docs derived from W01's committed code) follows it on Haiku. They cannot run in parallel: W02 reads W01's final wording.

### W01 (code: `register.tsx`, `register.test.ts`)

| Finding | Where | Before | After |
|---|---|---|---|
| **N6** (INFO) dead branch | `register.tsx` ~1360-1363, the `/clear` fold | `for (const entry of ring.entries) { if (isReplayable(entry.row)) s.foldedPending += 1; else if (entry.row.state === 'dead') s.foldedDead += 1 }` — the ring is only deleted when no entry is replayable, so the first branch never runs | only the `dead` counting and the `foldedDropped` fold remain; no behaviour change |
| **N4** (LOW) unbounded scan | `register.tsx:213-222`, `decisionsOf(answer)` | `answer.matchAll(DECISION_LINE)` on the whole answer | new constant `MAX_ANSWER_SCAN_CHARS = 200_000`; the matcher runs on `answer.slice(0, 200_000)`. A `Decision:` line beyond the bound is not captured (documented). Cost was already linear; this caps it. |
| **N3** (LOW) status | `register.tsx:624-663`, `renderStatus`; `foldedPending` set in `initSession` (~1138) | `pending` = own replayable rows **plus** earlier sessions' replayable rows read from disk at start, so `📮 N pending` can stick for rows this process never sends | `pending` counts only this process's own rows. Earlier sessions' unsent rows become a suffix ` · N left by earlier sessions` (omitted at 0, in `📮 memory-only` and in `⚠ outbox write failed`). Replay still walks only this process's rings; adopting another writer's file stays NOT_BUILT. |

Status texts after the change (examples): `📮 clear`, `📮 1 pending`, `📮 clear · 2 left by earlier sessions`, `📮 1 pending (ledger unavailable) · 2 left by earlier sessions`, `⚠ 1 undeliverable · 2 left by earlier sessions`.
Tests (TDD, failing run first): the prior-session test (~`register.test.ts:887-900`) moves to the new text; new tests for own-only counting, suffix at 0 and in the memory-only and failed forms, the 200,000-character bound (marker inside captured, marker after it not, a multi-megabyte answer still returns an early marker), and that earlier sessions' rows are still never emitted.

### W02 (docs: `README.md`, `docs/02-how-to/memory-bridge.md`)

- How-to section 3: `📮 N pending` now means this session's task or note rows waiting for the ledger; add the `left by earlier sessions` suffix, its meaning, and that those rows are not replayed (the "Not built" row for that stays). Add the 200,000-character scan bound to the decision-capture sentence. Stay at 149 lines or fewer (currently 147).
- README: the status-line table and the prose that says other sessions' pending rows are counted (currently around lines 106 and 151); the scan bound next to the decision-marker rule.
- No commit hash or PR number; the exact wording is derived from the committed W01 code, not pinned here.

Not in scope: N7 (never run live) and N8 (the `tool.call` hook's fire-and-forget observation) stay accepted notes; the replay, the ring file format, the band and `/bridge-note` behave exactly as before.

```
TP_ROUTE   (coordinator)
runner=claude-code-desktop
model=claude-sonnet-5-5
effort=high
skills=task-packet
why=session pin; issuing a two-workstream repair macro

TP_ROUTE   (W01)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=NONE
why=status-semantics change with test rewrites; Haiku did the string-level repairs, but this one needs judgment on tests; cost UNKNOWN

TP_ROUTE   (W02)
runner=claude-code-agent
model=claude-haiku-5-5   (fallback claude-sonnet-5-5 on an evidence-backed STOP only)
effort=UNKNOWN
skills=NONE
why=docs derived from committed code; cheapest adequate; the R3 docs repair ran on Haiku in 33 s
```

## PROPOSED allowances (accepted by authorizing R4)

| Scope | Elapsed | Subagent tokens | Tool uses | Attempts |
|---|---|---|---|---|
| W01 | 45 min | 500,000 | 120 | 1 Sonnet + 1 retry after a failed validation with a named cause |
| W02 | 20 min | 200,000 | 60 | 1 Haiku + 1 Sonnet fallback |
| **Macro** | 3 h to a frozen head | 1,000,000 | — | 4 dispatches; 1 team-lead correction round |

Basis: the original Sonnet build children used 332k-424k tokens for far larger work (W02 ~331k, W03 ~424k); this change touches three small areas plus tests, so 500k is generous. R3's Haiku docs child used 97k. Caps, not forecasts; cost UNKNOWN; active time is not recordable. Intermediate audits 0, `advisor` 0. Audit (outside the budget): 1 attempt, 0 retries, no fallback; the earlier runs cost about $0.08 and 3 minutes each. `ct validate-macro` does not check these numbers; the team lead does.

## Validation at issuance

| Check | Result |
|---|---|
| `ct validate-macro` | PASS, STATIC_VALID |
| `ct bind-record` + `ct validate-binding` (coordinator) | PASS |
| `task_packet.v2` schema W01, W02 | PASS ×2 |
| Macro pins (2 task packets + binding) | MATCH |
| Child bindings, DCP route, Task Orchestrator state | NOT_RUN (child bindings are created per child at dispatch) |

## What happens to the PR

Same as R3: new commits after `bff3fd46e`, a new audited subject, nothing pushed by me. After a passing audit you re-attest, re-sign at the final head and push. R3's signed-proof path is not needed if you decide to take R4 instead: R4 supersedes R3's repaired head, so only the final head needs attesting. Each further repair round makes the earlier unsigned proofs obsolete, so consider stopping after this one.
