# Task-Orchestrator Deep Audit — 2026-05-28

**Auditor**: Claude Code (read-only audit; no orchestrator state mutated)
**Scope**: All work-items, notes, gates, dependencies in the task-orchestrator MCP instance for workspace `/Users/hue/code/dopemux-mvp`, cross-referenced against git + open PRs.
**Branch at audit time**: `codex/tp-dmx-orch-007-plugin-hooks` (13 commits ahead of `main`)
**Method**: `get_context` (health + item), `query_items` (overview + get + FTS), `query_notes`, `query_dependencies`, `get_blocked_items`, `get_next_item` + git/gh cross-check. Sampled 10 of ~44 CLAUDE-SURFACE descendants + all DMX-ORCH-INTEGRATION children.

---

## Verdict

Orchestrator state is **trustworthy for one series and unreliable for the other**:

- ✅ **DMX-ORCH-CLAUDE-SURFACE** (`1b633d83`) — driven through the orchestrator faithfully (full PAL-chain notes, proof bundles, clean `complete`-gated transitions). This is the model of correct usage.
- ❌ **DMX-ORCH-INTEGRATION** (`32df1792`) — orchestrator largely **bypassed**. Real work shipped via git/PR #714, but work-item state does not reflect it: items force-terminal'd without proof bundles, completed code left sitting in `queue`, and the series root carries a false "done" label.
- ⚠️ **Three external / data-integrity issues** (in the orchestrator MCP itself, not repo code): (1) a malformed timestamp in the CLAUDE-SURFACE subtree breaks `count-children-by-role` and the overview API **fails silently to zero** (MED-1); (2) the health-check **under-reports blocked items as 0** while the dedicated tool finds 27 (MED-4); (3) a **dangling dependency edge** points at a missing item titled "Unknown" (MED-5).

The discipline divide is **temporal**: the loosely-tracked INTEGRATION work was processed ~2026-05-26 (before the `.taskorchestrator/config.yaml` schema/gate config was finalized 2026-05-27); the disciplined CLAUDE-SURFACE work is all 2026-05-27/28.

---

## Inventory — 5 root work-items

| Root ID | Title | Role | statusLabel | Children | Assessment |
|---|---|---|---|---|---|
| `b7bd0906` | dNh CRM v0.1 Accelerated Release Train | queue | — | 15 queue | Different project, parked, never started |
| `1dfbda2e` | Dopemux Repo Documentation Forge | terminal | done | 4 terminal | ✅ Clean / complete |
| `32df1792` | Task Orchestrator Integration into Daily Operator Workflow | **work** | **done** | 15 queue + 4 terminal | ❌ Desynced (see CRIT-1) |
| `3e4f09f3` | DMX-ORCH-INTEGRATION-FOLLOWUP — 9 follow-up packets | queue | — | 3 queue + 5 terminal | Mostly done; 3 genuine pending follow-ups |
| `1b633d83` | DMX-ORCH-CLAUDE-SURFACE | work | in-progress | ~44 (all sampled terminal) | ✅ Disciplined; root legitimately open (Phases 5–7 deferred). ⚠️ overview count broken (MED-1) |

---

## Findings register

### ORCH-AUDIT-CRIT-1 — DMX-ORCH-INTEGRATION state contradicts shipped reality
**Severity**: CRITICAL (for trust in the orchestrator as workflow authority)

The series that *implements* orchestrator integration is the one *not* tracked by the orchestrator. 13 commits on the current branch (open in PR #714, base `main`, **not merged**) implement TP-001 through TP-007, but the work-items say otherwise:

| Packet | Item ID | Orchestrator state | Git reality (branch `codex/tp-dmx-orch-007-plugin-hooks`) |
|---|---|---|---|
| TP-DMX-ORCH-001 (boundary reconcile) | `bb3d4208` | terminal / **in-progress** / 0 notes | commit `c322586f8` |
| TP-DMX-ORCH-002 (daily status CLI) | `0d6c6799` | terminal / **in-progress** / 0 notes | commit `3958550c3` |
| TP-DMX-ORCH-003 (packet+proof validators) | `8fb2c458` | terminal / **in-progress** / 1 work note, no proof | commit `2e787b215` |
| TP-DMX-ORCH-004 (approval policy) | `2e4ec157` | terminal / **done** | commit `6a1b71ecc` ✅ only clean one |
| TP-DMX-ORCH-005 (MCP wrappers) | `f025275f` | **queue** / unstarted | commit `8bf1431fd` |
| TP-DMX-ORCH-006 (DSL validator) | `47ceb6ab` | **queue** / unstarted | commits `655742368`, `b772f477f` |
| TP-DMX-ORCH-007 (plugin+hook registry) | `409dff3e` | **queue** / unclaimed / 0 notes / never transitioned | commit `317457c40` (+ branch is literally named for it) |

**Impact**: The orchestrator cannot be relied on to answer "what is the state of DMX-ORCH-INTEGRATION?" — it under-reports (005/006/007 look untouched) and over-reports (001/002/003 look terminal). Per AGENTS.md §6 + §12 + the accepted workflow-authority ADR, this is the orchestrator failing its canonical role for in-flight work.
**Aggravating**: the *plan structure* WAS built carefully — the full BLOCKS dependency graph exists (TP-001→…→TP-017 linearized with fan-out/fan-in; `query_dependencies` confirms TP-004→007, TP-006→007, 007→008, 007→009, etc.). So this is not lazy setup; it is a carefully-planned tree whose **execution tracking was then abandoned**. Worse, the work shipped **out of dependency order**: TP-007's code is committed (`317457c40`) while its declared blocker TP-006 is still `queue` (unsatisfied) — the orchestrator's blocked-state is fiction relative to git.
**Evidence**: `query_items get` on each ID; `query_dependencies get itemId=409dff3e`; `git log main..HEAD`; `gh pr view 714` (OPEN, unmerged).
**Recommended (NOT executed)**: reconcile after PR #714 merges — claim+start+proof-bundle+complete TP-005/006/007; back-fill proof-bundle notes on 001/002/003 (or `reopen`→`complete` to pass the gate); fix the root label (see MED-3).

### ORCH-AUDIT-HIGH-1 — TP-001/002/003 reached terminal bypassing the complete-gate
**Severity**: HIGH

All three are `role=terminal` with `statusLabel="in-progress"` and **no `proof-bundle` note** (TP-002, TP-001: 0 notes; TP-003: only an `implementation-start` work note). This state is **unreachable via `advance_item(trigger="complete")`**, which (a) requires the `proof-bundle` note (config line 317-331, `required: true`) and (b) sets `statusLabel="done"` (config line 625). The residual "in-progress" label is what `start` leaves behind. The only path that produces `terminal` + `in-progress` + no-proof is a **direct `manage_items` role mutation** (gates fire only on `advance_item` triggers — config line 21), or processing before the gate config was deployed.
**Mitigating nuance**: these items were worked ~2026-05-26 (TP-007 `createdAt` `2026-05-26T13:21:33Z`); the schema config `updated_at` is `2026-05-27`. Plausibly the gate simply wasn't enforced yet — "pre-gate legacy state" rather than willful bypass. Either way the records are non-compliant with AGENTS.md §9 today.
**Evidence**: `query_notes list` (role=review) on all three; `.taskorchestrator/config.yaml` status_labels + task-packet schema.

### ORCH-AUDIT-HIGH-2 — Active branch is orphaned from its work-item
**Severity**: HIGH

Current branch `codex/tp-dmx-orch-007-plugin-hooks` carries the TP-007 deliverable (commit `317457c40 feat(orchestrator): add plugin hook registry`), yet TP-007 (`409dff3e`) is `role=queue`, **never claimed, never started, 0 notes**, with `createdAt == modifiedAt == roleChangedAt == 2026-05-26T13:21:33Z` (no transition ever). Per §12 Orchestrator Operations, in-flight work should be reflected as a claimed/`work`-role item. This is drift **in progress right now**, not historical.
**Evidence**: `get_context itemId=409dff3e`; `git branch --show-current`; `git log`.

### ORCH-AUDIT-MED-1 — External orchestrator MCP: malformed timestamp breaks subtree aggregation, fails silently
**Severity**: MEDIUM · **Authority**: external Kotlin MCP (`/Users/hue/plugins/dopemux-mission-control/...`), **outside repo authority** per AGENTS.md §6 — observe & report only.

Two independent symptoms, one root cause:
1. `query_items(operation=overview, itemId=1b633d83)` → **`Query failed: Failed to count children by role: Error parsing time stamp`**.
2. Global `query_items(operation=overview)` returned `childCounts: {all zero}` and `children: []` for `1b633d83` — **silently wrong** (the same count-by-role failed but was swallowed to zeros), while `claimSummary.unclaimed: 43` (computed by a different path) correctly reflected ~44 descendants. FTS confirmed 44 descendants + root.

A malformed timestamp on one descendant breaks the aggregate count query. The global overview's **fail-to-zero** behavior is the more dangerous defect: it presents a populated 44-item subtree as empty (`0/0/0/0/0`) with no error — a misleading-success violation of the deterministic-systems doctrine. The corrupt record was **not isolated** (10 sampled descendants + the root all have clean ISO timestamps; locating it would require enumerating all ~44, deliberately not done).
**Recommended (NOT executed)**: operator isolate the bad record via targeted DB query and report upstream; the overview API should fail loudly, not to zero.

### ORCH-AUDIT-MED-2 — CLAUDE-SURFACE root stuck in `work`; auto-cascade possibly impaired
**Severity**: MEDIUM · partly **UNKNOWN**

Root `1b633d83` is `role=work`; all 10 sampled children are `terminal`, and `get_next_item` returns 0 for queue/work/review under it (control parent `32df1792` correctly returned 3 — so the tool works and CLAUDE-SURFACE genuinely has no active items in those roles). Two non-exclusive explanations:
- **Correct**: the series plans 68 TPs across Phases 1–7 (~44 created, Phases 5–7 deferred; Phase 7 intentionally blocked). A series root *should* stay open. ✅ likely.
- **Bug**: default-schema lifecycle is `AUTO` (cascade parent→terminal when all children terminal). If all existing children are terminal, cascade should have fired — unless the same count-by-role failure (MED-1) silently prevents it. **UNKNOWN** which dominates; flagged because the two interact.

### ORCH-AUDIT-MED-3 — Series root `32df1792` shows `statusLabel=done` while `role=work` with 15 queued children
**Severity**: MEDIUM

A false-"done" signal: the DMX-ORCH-INTEGRATION root reads `done` while it remains in `work` with 15 of 19 children still in `queue` and only 1 child (TP-004) legitimately complete. `role=work` + `statusLabel=done` is not a normal `advance_item` outcome (`complete`/`cascade` set `done` only alongside `role=terminal`). Consistent with the CRIT-1 loose-tracking pattern.

### ORCH-AUDIT-MED-4 — Health-check under-reports blocked items (0) vs dedicated tool (27)
**Severity**: MEDIUM · **Authority**: external Kotlin MCP — observe & report.

`get_context(mode="health-check")` returned `blockedItems: []`, but `get_blocked_items()` returned **27 blocked items** (all `blockType="dependency"`). The health-check appears to count only explicit `BLOCKED`-role items and omits dependency-blocked ones. Per `.claude/CLAUDE.md` the discovery sequence for a fresh session is "`get_context()` health-check" **first** — so an operator opening the project sees a false "all clear" (0 blocked) when 27 items are in fact dependency-blocked. Use `get_blocked_items` for true blocked state.
**Evidence**: `get_context mode=health-check` vs `get_blocked_items includeDetails=true`.

### ORCH-AUDIT-MED-5 — Dangling dependency edge to a missing item ("Unknown")
**Severity**: MEDIUM

`TP-DMX-ORCH-017-FINAL` (`1cc65d37`) has a `BLOCKS` edge from item `82aaf3b5-bca4-49e5-ae03-e1865a451012`, but that item resolves to **`title: "Unknown"`** — a dangling reference to an item that does not exist / was deleted without cleaning its edges. This is the resolution of OBS-1: the FOLLOWUP root claims "9 follow-up packets" but only 8 exist; the phantom 9th (`82aaf3b5`) survives only as an orphaned dependency edge. A foreign-key-style integrity gap in the dependency graph.
**Evidence**: `get_blocked_items` (017-FINAL `blockedBy` list includes `82aaf3b5` / "Unknown").

### ORCH-AUDIT-LOW-1 — Inconsistent `type` field across task-packets
**Severity**: LOW

Most TP-CS items carry `type="task-packet"`; some do not (e.g., `3ad6fc5c` TP-CS-037). Per config §schema-selection, a missing `type` falls through tag-fallback to the **`default`** schema instead of `task-packet`. Both still hard-gate on `proof-bundle`, so functional impact is limited, but PAL-chain advisory notes differ between the two schemas — selection should be deterministic.

### ORCH-AUDIT-OBS-1 — FOLLOWUP root title/count drift (root-caused by MED-5)
Root `3e4f09f3` is titled "…**9** follow-up packets" (seeded via open PR #716) but has **8** children (5 terminal + 3 queue: 014A-UPSTREAM, 016-DAEMON, 017-FINAL). Root cause is the dangling item `82aaf3b5` ("Unknown") in MED-5 — the 9th packet was referenced (as a dependency) but never persisted as a child. Not cosmetic; see MED-5.

### ORCH-AUDIT-OBS-2 — Foreign project parked in the instance
Root `b7bd0906` "dNh CRM v0.1 Accelerated Release Train" (15 lanes, all `queue`, never started) appears unrelated to dopemux orchestrator work — a different project sharing the same orchestrator instance. Noted for hygiene; out of audit scope.

### ORCH-AUDIT-OBS-3 — Positive: CLAUDE-SURFACE + Documentation Forge are exemplary
TP-CS-019 (`ea3c7e75`) carries the full note set — `analyze`, `planner`, `codereview`, `implementation-evidence`, `precommit`, `proof-bundle` — and went terminal cleanly; TP-CS-044 has its `proof-bundle`. Documentation Forge (`1dfbda2e`) is fully terminal/done. These demonstrate the gate working as designed and should be the template for reconciling DMX-ORCH-INTEGRATION.

---

## Validation performed (PASS / FAIL / NOT_RUN)

- **PASS** — Enumerated all 5 roots; characterized every DMX-ORCH-INTEGRATION child; sampled 10/44 CLAUDE-SURFACE descendants (all terminal/done, valid timestamps); confirmed proof-bundle presence/absence via `query_notes`; cross-checked 13 branch commits + PR #714 (OPEN) + open-PR list; confirmed `get_next_item` works on control parent; walked the BLOCKS dependency graph via `get_blocked_items` (27 dependency-blocked items) + `query_dependencies` on TP-007.
- **FAIL (reproduced, external)** — `query_items overview itemId=1b633d83` → "Error parsing time stamp"; global overview silently zeros CLAUDE-SURFACE childCounts (MED-1).
- **NOT_RUN** — Exact corrupt-timestamp record not isolated (would require enumerating ~34 unsampled descendants; external infra bug). Role of the ~34 unsampled CLAUDE-SURFACE items assumed terminal by inference, not verified per-item. `manage_dependencies`/`query_dependencies` graph not exhaustively walked (no blocked items found, so low risk). Whether TP-CS items behind open PRs #722 (TP-CS-060/061/110) are correctly `queue` vs `terminal` not checked.

## Remaining uncertainty
- The *mechanism* by which TP-001/002/003 and root `32df1792` got their anomalous labels is inferred (direct `manage_items` mutation and/or pre-gate processing), not directly observed.
- MED-2 cascade question is genuinely UNKNOWN pending MED-1 isolation.

## Recommended next steps (require operator decision — none executed)
1. **After PR #714 merges**: reconcile DMX-ORCH-INTEGRATION — proof-bundle + complete TP-005/006/007; back-fill or `reopen→complete` TP-001/002/003; correct root `32df1792` label.
2. **Escalate MED-1** to the orchestrator MCP maintainer: malformed timestamp + fail-to-zero overview behavior.
3. Decide whether the dNh CRM tree (OBS-2) belongs in this instance.
4. Standardize `type="task-packet"` on all packets (LOW-1).
