# TP-REPLAN-BASELINE-1182-VALIDATE — operator return

## Exact-head verdict

| Field | Value |
|---|---|
| PR | [#1182](https://github.com/DDD-Enterprises/dopemux-mvp/pull/1182) |
| Head | `b457505ddd5d321374caedeec847947f64e911c8` |
| Class | **REPLAN_BASELINE_CANDIDATE** |
| Verdict | **HOLD** — not READY, not COMPLETE, not PASS |
| Wave 0 | **Do not dispatch** |
| DB mutation | **Do not continue** |

Worktree: `.worktrees/TP-REPLAN-BASELINE-1182-VALIDATE` on `codex/tp-replan-baseline-1182-validate`.

## Six-file scope reconciliation

Handoff said **2 files**. PR has **6**.

| Slice | Files |
|---|---|
| Commit B replan export | `MASTER-PLAN.md`, `routing-table.json` |
| Commit A inherited defrag/load-plan | defrag doc, index link, two load-plan LOADED backfills |

**Recommendation: KEEP all six**; update handoff/scope/validation/rollback. Do not split unless operator wants pure routing-only PR (then split commit A out explicitly).

## Reproduced count ledger

| Metric | Value | Status |
|---|---|---|
| Non-terminal items | **539** | exact |
| PR body “~520” | prose only | **correct to 539** |
| Untagged (`wave=null`) | **39** | matches summary |
| Wave 0 | **32** | matches |
| Verify-close | **77** | matches |
| Verify-close multi-wave? | **YES** | 12/62/1/1/1 on waves 0/2/3/4/5 |
| Luna-ready | **51** | matches |
| 500 waves + 39 untagged | **539** | PASS |

`summary.by_primary_runner` does **not** reproduce cleanly (declared `none=201` + splits malformed `+rec-*` tokens).

## Deterministic routing checks

| Check | Result |
|---|---|
| JSON parse / structure | PASS |
| Unique IDs | PASS |
| Summary totals/waves/flags/untagged | PASS |
| Exactly one primary pair per actionable leaf | **FAIL** (102 missing; 2 malformed double-rec; 7 runner-only) |
| Exactly one backup pair | **FAIL** (many null; 25 model-only; 6 gemini runner-only) |
| No runners on operator-gate | **FAIL** (2 items tagged) |
| Dependencies resolve | **NOT_CHECKABLE** (absent from export) |

## Sampling results

### Verify-close (5 programs)

| ID | Program | Verdict |
|---|---|---|
| b807751c | Beta SEC-01 LiteLLM | **FAIL/PARTIAL** — env key fixed; port still not loopback-bound |
| 59d66926 | Beta DOCS-01 Start Here | **PASS** |
| 0890be0d | DCP-TOOLING TP-102 | **PASS** (PR #885 merged) |
| aafc2630 | CONPORT-OPTIMAL-002 | **UNKNOWN** (PR #894 mapping weak) |
| 207ec91a | TO-CONPORT supervisor review | **UNKNOWN** (impl merged; supervisor receipt missing) |

Observed caution rate **3/5** → Wave 0A **not cleared**.

### Luna-ready (3 classes)

| ID | Class | Verdict |
|---|---|---|
| cb674145 | MCP healthcheck TP | **PASS_STRUCTURE** |
| 12a034e1 | Dependabot fastmcp bump | **FAIL_STRUCTURE** (no TP; lock still 2.14.0) |
| 233bb86e | Destructive ADHD delete | **FAIL_STRUCTURE** + operator-gate class |

## Audit / Steward / CI

| Gate | Verdict | Evidence |
|---|---|---|
| Independent embedded audit | **FAIL** `NEEDS_SUPERVISOR` | run 30769383066; auditor tool/model **unknown** → stop |
| PR Steward | **NOT READY** | run 30769399625; steward skipped after audit fail |
| Complete CI pipeline | mostly green | red only audit + steward |

## #1136 repair recommendation

Do **not** admin-merge.

Bounded packet: `task-packets/TP-RTE-TRUTH-1136-REPAIR-001.json`

- 366 files confirmed (paginate past 100)
- 1 removal → clobber LARGE_DELETION; needs human `intentional-deletion` label
- Refresh vs current main without force-push
- Re-audit + Steward on final head
- Rerun RTE + full CI

## Stacked follow-up PR

| Field | Value |
|---|---|
| URL | https://github.com/DDD-Enterprises/dopemux-mvp/pull/1183 |
| Base | `claude/rte-truth-program` (not main) |
| Head | `claude/rte-truth-followup` @ `a8faf22b49` |
| Delta | 6 commits |
| State | **draft** |
| Retarget | only after #1136 lands + refresh/revalidate |

## Next operator actions (max 3)

1. Accept HOLD on #1182; authorize routing-table/PR-body repairs + independent audit with recorded model identity.
2. On #1136: confirm intentional deletion of `user-journey.md`, add label, run repair packet (no admin-merge).
3. Keep #1183 draft stacked; ignore Wave 0 until #1182 READY.
