# Task-Orchestrator Deep Audit + Reconciliation — 2026-05-28

> **Provenance / volatility note:** This file was written, lost, and recreated within one session. A **concurrent process checked out branch `claude/upbeat-thompson-35f2e8` (PR #718) in the shared working directory** mid-session (git reflog `HEAD@{3}: checkout: moving from codex/tp-dmx-orch-007-plugin-hooks to claude/upbeat-thompson-35f2e8`), which wiped the original untracked copy. `claudedocs/` is not gitignored, so a copy here remains volatile. A durable backup exists at `~/.claude/projects/-Users-hue-code-dopemux-mvp/memory/orchestrator_audit_2026_05_28_FULL.md`. The orchestrator reconciliation (below) lives in the MCP's own DB and is unaffected by the working-tree branch switch.

**Auditor**: Claude Code · **Scope**: all work-items, notes, gates, dependency graph in the task-orchestrator MCP for workspace `/Users/hue/code/dopemux-mvp`, cross-referenced against git + open PRs.
**Audited from branch**: `codex/tp-dmx-orch-007-plugin-hooks` (13 commits ahead of `main`; the working tree was later switched away by another process — see note above; the branch + PR #714 still exist).
**Method**: `get_context` (health + item), `query_items` (overview + get + FTS), `query_notes`, `query_dependencies`, `get_blocked_items`, `get_next_item`, `get_next_status` + git/gh cross-check. Sampled 10 of ~44 CLAUDE-SURFACE descendants + all DMX-ORCH-INTEGRATION children.

---

## Verdict

Orchestrator state was **trustworthy for one series and unreliable for the other**; the unreliable one has now been reconciled (see §Reconciliation executed):

- ✅ **DMX-ORCH-CLAUDE-SURFACE** (`1b633d83`) — driven through the orchestrator faithfully (full PAL-chain notes, proof bundles, clean `complete`-gated transitions). Model of correct usage.
- ❌→🟡 **DMX-ORCH-INTEGRATION** (`32df1792`) — orchestrator was bypassed; **now reconciled to honest in-flight state** (work-role + evidence notes), with completion correctly deferred until PR #714 merges.
- ⚠️ **Three external / data-integrity issues in the orchestrator MCP itself**: (1) malformed timestamp breaks `count-children-by-role` and the overview **fails silently to zero** (MED-1); (2) health-check **under-reports blocked items as 0** while the real count is 27 (MED-4); (3) a **dangling dependency edge** to a missing item "Unknown" (MED-5) — **fixed during reconciliation**.

Discipline divide is temporal: loosely-tracked INTEGRATION work was processed ~2026-05-26 (before `.taskorchestrator/config.yaml` gates finalized 2026-05-27); disciplined CLAUDE-SURFACE work is 05-27/28.

---

## Inventory — 5 root work-items

| Root ID | Title | Role | statusLabel | Children | Assessment |
|---|---|---|---|---|---|
| `b7bd0906` | dNh CRM v0.1 Accelerated Release Train | queue | — | 15 queue | Different project, parked, never started (OBS-2) |
| `1dfbda2e` | Dopemux Repo Documentation Forge | terminal | done | 4 terminal | ✅ Clean / complete |
| `32df1792` | Task Orchestrator Integration into Daily Operator Workflow | work | in-progress* | 15 queue + 4 terminal | ❌→🟡 was desynced (CRIT-1); *label fixed during reconciliation |
| `3e4f09f3` | DMX-ORCH-INTEGRATION-FOLLOWUP — 9 follow-up packets | queue | — | 3 queue + 5 terminal | Mostly done; 3 genuine pending follow-ups; phantom 9th = MED-5 |
| `1b633d83` | DMX-ORCH-CLAUDE-SURFACE | work | in-progress | ~44 (all sampled terminal) | ✅ Disciplined; root legitimately open (Phases 5–7 deferred). ⚠️ overview count broken (MED-1) |

---

## Findings register

### ORCH-AUDIT-CRIT-1 — DMX-ORCH-INTEGRATION state contradicted shipped reality
**Severity**: CRITICAL · **Status**: RECONCILED (in-flight model)

The series that *implements* orchestrator integration was the one *not* tracked by the orchestrator. 13 commits (open in PR #714, base `main`, **not merged**) implement TP-001→007, but the work-items said otherwise:

| Packet | Item ID | Orchestrator state (at audit) | Git reality (branch `codex/tp-dmx-orch-007-plugin-hooks`) |
|---|---|---|---|
| TP-001 (boundary reconcile) | `bb3d4208` | terminal / **in-progress** / 0 notes | `c322586f8` |
| TP-002 (daily status CLI) | `0d6c6799` | terminal / **in-progress** / 0 notes | `3958550c3` |
| TP-003 (packet+proof validators) | `8fb2c458` | terminal / **in-progress** / 1 work note, no proof | `2e787b215` |
| TP-004 (approval policy) | `2e4ec157` | terminal / **done** | `6a1b71ecc` ✅ only clean one |
| TP-005 (MCP wrappers) | `f025275f` | **queue** / unstarted | `8bf1431fd` |
| TP-006 (DSL validator) | `47ceb6ab` | **queue** / unstarted | `655742368`, `b772f477f` |
| TP-007 (plugin+hook registry) | `409dff3e` | **queue** / unclaimed / 0 notes / never transitioned | `317457c40` (+ branch named for it) |

**Aggravating**: the *plan structure* was built carefully — the full BLOCKS dependency graph exists (TP-001→…→TP-017 linearized with fan-out/fan-in). So this was not lazy setup; it was a carefully-planned tree whose **execution tracking was abandoned**. Worse, work shipped **out of dependency order**: TP-007's code is committed while its declared blocker TP-006 was still `queue`.
**Evidence**: `query_items get` on each ID; `query_dependencies get itemId=409dff3e`; `git log main..HEAD`; `gh pr view 714` (OPEN, unmerged).

### ORCH-AUDIT-HIGH-1 — TP-001/002/003 reached terminal bypassing the complete-gate
**Severity**: HIGH · **Status**: documented; items left terminal (see §Reconciliation rationale)

All three are `role=terminal` with `statusLabel="in-progress"` and **no `proof-bundle` note**. This state is unreachable via `advance_item(trigger="complete")`, which requires the proof-bundle note (config L317-331) and sets `statusLabel="done"` (config L625). Consistent with direct `manage_items` role mutation or pre-gate processing.
**Mitigating nuance**: worked ~2026-05-26; schema config `updated_at` is 2026-05-27 — plausibly the gate wasn't enforced yet ("pre-gate legacy state").
**Evidence**: `query_notes list role=review` on all three; `.taskorchestrator/config.yaml`.

### ORCH-AUDIT-HIGH-2 — Active branch was orphaned from its work-item
**Severity**: HIGH · **Status**: RECONCILED (evidence note added; TP-007 stays queue, correctly blocked)

Branch `codex/tp-dmx-orch-007-plugin-hooks` carries the TP-007 deliverable (`317457c40`), yet TP-007 (`409dff3e`) was `role=queue`, never claimed/started, 0 notes, `createdAt==modifiedAt==roleChangedAt`. TP-007 is also genuinely BLOCKS-blocked by TP-006 (unblockAt=terminal), so it cannot `start` until TP-006 completes — the work shipped out of order.
**Evidence**: `get_context itemId=409dff3e`; `get_next_status` (Blocked by TP-006); `git`.

### ORCH-AUDIT-MED-1 — External MCP: malformed timestamp breaks subtree aggregation, fails silently
**Severity**: MEDIUM · **Authority**: external Kotlin MCP — observe & report (see §Bugfix plan)

`query_items(overview, itemId=1b633d83)` → `Failed to count children by role: Error parsing time stamp`. Global overview returned `childCounts: {all zero}` + `children: []` for `1b633d83` (silently wrong — the same count-by-role failed but was swallowed to zeros), while `claimSummary.unclaimed: 43` correctly reflected ~44 descendants. The **fail-to-zero** behavior is the dangerous defect: it presents a 44-item subtree as empty with no error. Corrupt record **not isolated** (10 sampled descendants + root all had clean timestamps; isolating it needs full enumeration).

### ORCH-AUDIT-MED-2 — CLAUDE-SURFACE root stuck in `work`; auto-cascade possibly impaired
**Severity**: MEDIUM · partly **UNKNOWN**

Root `1b633d83` is `role=work`; all 10 sampled children are terminal; `get_next_item` returns 0 for queue/work/review there (control parent `32df1792` correctly returned 3 — tool works). Two non-exclusive explanations: (a) **correct** — 68 TPs planned, ~44 created, Phases 5–7 deferred, so the root should stay open; (b) **bug** — default-schema lifecycle is AUTO, so cascade should fire if all children terminal, unless MED-1's count failure silently prevents it. UNKNOWN which dominates.

### ORCH-AUDIT-MED-3 — Series root `32df1792` showed `statusLabel=done` while `role=work`
**Severity**: MEDIUM · **Status**: FIXED during reconciliation (label → "in-progress")

A false-"done" signal while the root remained `work` with 15 of 19 children in `queue`. `role=work` + `statusLabel=done` is not a normal `advance_item` outcome.

### ORCH-AUDIT-MED-4 — Health-check under-reports blocked items (0) vs dedicated tool (27)
**Severity**: MEDIUM · **Authority**: external MCP — observe & report (see §Bugfix plan)

`get_context(mode="health-check")` returned `blockedItems: []`, but `get_blocked_items()` returned **27** (all `blockType="dependency"`). Health-check appears to count only explicit `BLOCKED`-role items. Per `.claude/CLAUDE.md`, a fresh session runs the health-check first — so it sees a false "all clear." Confirmed still present after reconciliation.

### ORCH-AUDIT-MED-5 — Dangling dependency edge to a missing item ("Unknown")
**Severity**: MEDIUM · **Status**: FIXED during reconciliation (edge deleted)

`TP-DMX-ORCH-017-FINAL` (`1cc65d37`) had a `BLOCKS` edge from item `82aaf3b5-…` which resolves to **`WorkItem not found`** — a dangling reference to a deleted item. This is the resolution of OBS-1 (FOLLOWUP "9 packets" but 8 children — the phantom 9th survived only as an orphaned edge). Verified missing via `query_items get` (404) before deletion.

### ORCH-AUDIT-LOW-1 — Inconsistent `type` field across task-packets
**Severity**: LOW

Most TP-CS items carry `type="task-packet"`; some don't (e.g., `3ad6fc5c` TP-CS-037), falling through to the `default` schema instead of `task-packet`. Both still gate on `proof-bundle`, so impact is limited, but PAL-chain advisory notes differ between schemas.

### ORCH-AUDIT-OBS-1 — FOLLOWUP root title/count drift (root-caused by MED-5)
Root `3e4f09f3` titled "…**9** follow-up packets" but had **8** children. Root cause = the dangling `82aaf3b5` of MED-5 (now removed).

### ORCH-AUDIT-OBS-2 — Foreign project parked in the instance
Root `b7bd0906` "dNh CRM v0.1 Accelerated Release Train" (15 lanes, all `queue`, full dependency chain, never started) is unrelated to dopemux orchestrator work — a different project sharing the instance. Out of scope; noted for hygiene.

### ORCH-AUDIT-OBS-3 — Positive: CLAUDE-SURFACE + Documentation Forge are exemplary
TP-CS-019 (`ea3c7e75`) has the full note set (analyze, planner, codereview, implementation-evidence, precommit, proof-bundle) and went terminal cleanly; TP-CS-044 has its proof-bundle. Documentation Forge fully terminal/done. Template for reconciling DMX-ORCH-INTEGRATION post-merge.

---

## Reconciliation executed (2026-05-28, operator-directed)

User authorized "reconcile and plan bugfixes." Reconciliation followed the **§9-honest in-flight model**: unmerged work (PR #714 OPEN) must NOT be marked `done`. All writes used actor `{id: "operator-audit-reconcile-2026-05-28", kind: "user", parent: "orchestrator-audit-2026-05-28"}` with per-action idempotency `requestId`s.

| # | Action | Tool | Result |
|---|---|---|---|
| 1 | Root `32df1792` `statusLabel` "done" → "in-progress" (fix MED-3) | `manage_items update` | `updated:1` ✅ |
| 2 | Delete dangling `82aaf3b5`→`1cc65d37` BLOCKS edge (fix MED-5) | `manage_dependencies delete` | `deleted:1` ✅ (verified item 404 first) |
| 3 | `implementation-evidence` notes on TP-001…007 (7 items, commit SHAs + PR #714 + deferral rationale) | `manage_notes upsert` | `upserted:7` ✅ |
| 4 | TP-005 (`f025275f`) claim → `start` queue→work | `claim_item` + `advance_item` | role=work ✅ |
| 5 | TP-006 (`47ceb6ab`) claim → `start` queue→work | `claim_item` + `advance_item` | role=work ✅ |
| 6 | Release all transient claims | `claim_item releases` | active claims = 0 ✅ |

**Deliberately NOT done** (rationale):
- TP-005/006/007 **not** completed → PR #714 unmerged; marking `done` violates §9. Completion deferred until merge.
- TP-007 **left in queue** → genuinely blocked by TP-006 (needs terminal). The dep graph is correct; only the *history* was out of order, now documented in its note. Did not artificially unblock.
- TP-001/002/003 **left terminal** (not reopened) → code shipped, role tells the truth, label is cosmetic. Reopening would churn 3 items and risk breaking dependency-satisfaction for TP-009/010/011/etc. that point at them as `terminal=satisfied`. Operator to decide label/proof backfill post-merge.

**Post-reconciliation validation** (re-queried): root `32df1792` statusLabel="in-progress" ✅; TP-005/006 role=work ✅; TP-007 still `Blocked` by TP-006(work) ✅; TP-017-FINAL incoming deps 8→7, phantom gone ✅; `claimSummary {active:0, expired:0}` ✅.

---

## Bugfix plan — external orchestrator MCP (Kotlin, outside repo authority)

These live in the upstream Kotlin task-orchestrator (`jpicklyk/task-orchestrator` family; wrapper at `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`). Cannot be fixed from this repo — file upstream. Per AGENTS.md §6, do not modify the external wrapper without authorization.

**BUG-1 (from MED-1) — timestamp parse failure + fail-to-zero aggregation**
- *Symptom*: `query_items(overview, itemId=1b633d83)` throws `Failed to count children by role: Error parsing time stamp`; global overview returns `childCounts` all-zero for the same root instead of erroring.
- *Repro*: overview (scoped + global) over the CLAUDE-SURFACE subtree (~44 descendants).
- *Suspected cause*: one descendant has a timestamp column value that fails the Kotlin date parser; the count-by-role aggregation propagates the throw in scoped mode but swallows it to 0 in global mode.
- *Suggested fix*: (a) make global overview fail loud, never substitute 0 on aggregation error; (b) defensive parse with explicit null/format handling + log the offending itemId; (c) a DB migration/repair to normalize the bad timestamp.

**BUG-2 (from MED-4) — health-check omits dependency-blocked items**
- *Symptom*: `get_context(mode=health-check)` → `blockedItems: []` while `get_blocked_items()` → 27.
- *Suspected cause*: health-check enumerates only explicit `BLOCKED`-role items, not QUEUE/WORK/REVIEW items with unsatisfied blocking deps.
- *Suggested fix*: health-check should reuse `get_blocked_items` logic (both blockType="explicit" and "dependency"), or document that health-check `blockedItems` is explicit-only and rename accordingly.

**BUG-3 (from MED-5) — orphaned dependency edges survive item deletion**
- *Symptom*: a BLOCKS edge referenced `82aaf3b5` which is `WorkItem not found`; surfaced as a phantom blocker titled "Unknown".
- *Suspected cause*: item deletion does not cascade-delete its dependency edges (no FK ON DELETE CASCADE / no app-level cleanup).
- *Suggested fix*: cascade-delete edges on item delete; add an integrity sweep to drop edges whose endpoints don't exist; render unresolved endpoints as an explicit error, not silent "Unknown".

---

## Validation performed (PASS / FAIL / NOT_RUN)

- **PASS (audit)** — enumerated all 5 roots; characterized every DMX-ORCH-INTEGRATION child; sampled 10/44 CLAUDE-SURFACE descendants; confirmed proof-bundle presence/absence; cross-checked 13 branch commits + PR #714 (OPEN); confirmed `get_next_item` works on control parent; walked the dependency graph (27 blocked items) + `query_dependencies`.
- **PASS (reconciliation)** — all 6 write actions returned success; post-state re-queried and matches intent (see §Reconciliation validation row).
- **FAIL (reproduced, external)** — `query_items overview itemId=1b633d83` (timestamp); health-check blocked under-report (0 vs 27).
- **NOT_RUN** — exact corrupt-timestamp record not isolated (external infra); ~34 unsampled CLAUDE-SURFACE items' roles inferred, not verified per-item; TP-CS items behind open PRs #722 (060/061/110) not checked; no code/tests run (no repo code changed).

## Remaining uncertainty
- Mechanism of the original label anomalies is inferred (direct `manage_items` mutation and/or pre-gate), not directly observed.
- MED-2 cascade question is genuinely UNKNOWN pending MED-1 isolation.
- The working tree was switched to another branch by a concurrent process mid-session; this report's git references describe the persistent `codex/tp-dmx-orch-007-plugin-hooks` branch + PR #714 (which still exist), not necessarily the currently-checked-out tree.

## Recommended next steps
1. **After PR #714 merges**: fill `proof-bundle` notes + `complete` TP-005/006, then TP-007 (after TP-006 terminal); decide TP-001/002/003 label/proof backfill. (Reconciliation already moved 005/006 to work.)
2. **File the three external-MCP bugs** (§Bugfix plan) upstream.
3. **Mitigate the shared-working-directory hazard**: this repo has 30+ worktrees and concurrent agents actively check out branches in the main tree. Strongly consider isolating each agent session in its own worktree to prevent the mid-session branch-switch that ate this file.
4. Decide whether the dNh CRM tree (OBS-2) belongs in this instance; standardize `type="task-packet"` on all packets (LOW-1).
