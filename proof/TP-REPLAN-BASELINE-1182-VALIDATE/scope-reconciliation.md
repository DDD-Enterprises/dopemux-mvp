# Six-file scope reconciliation (PR #1182)

## Observed commits

| Commit | Message | Files |
|---|---|---|
| `a905161eb0` | docs(orchestrator): record DB defragmentation + backfill load-plan state | **4 files** |
| `b457505ddd` | replan(orchestrator): full 539-item wave+runner+luna-ready annotation | **2 files** |

## Handoff vs PR

| Claim | Value |
|---|---|
| Handoff reported | **2 files** (replan-only) |
| PR changed files | **6 files** |
| Gap | **4 inherited DB-defragmentation / load-plan files** from commit 1 |

## File classification

### Replan core (matches handoff “two files”)

1. `claudedocs/orchestrator-replan-2026-08-02/MASTER-PLAN.md` — ADDED
2. `claudedocs/orchestrator-replan-2026-08-02/routing-table.json` — ADDED

### Inherited DB-defrag / load-plan (four files)

3. `docs/03-reference/orchestrator-integration/db-defragmentation-2026-08-01.md` — ADDED
   Narrative of 2026-08-01 live load + defrag operation.
4. `docs/03-reference/orchestrator-integration/index.md` — MODIFIED
   Index link to the defrag doc.
5. `docs/ops/load-plans/load_plan-DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED.json` — MODIFIED
   Backfill: `live_task_orchestrator_load=LOADED`, root/leaf UUIDs, evidence pointer to defrag doc.
6. `docs/ops/load-plans/load_plan-TO-CANON.json` — MODIFIED
   Same class of LOADED backfill + leaf UUID map.

## Recommendation

**KEEP the four files in this PR** (do not split) **and update handoff/scope/validation/rollback** to describe a two-commit baseline:

1. **Commit A — operational truth**: defrag report + load-plan backfill (already performed 2026-08-01).
2. **Commit B — frozen routing export**: MASTER-PLAN + routing-table.json.

### Why not split

- Load-plan backfills are the durable **receipt** that the replan population exists in the orchestrator DB.
- Splitting would leave the replan export without its load-state authority, increasing operator confusion.
- All six files are docs/load-plan only — no runtime code risk from co-shipping.

### Required doc repairs before READY

- PR description: `~520` → **539**.
- Handoff / MASTER-PLAN scope line: “two files” → **six files / two commits**.
- Validation checklist: include load-plan JSON parse + LOADED field assertions.
- Rollback: reverse commit B for routing freeze; reverse commit A only if load-plan receipts must be unwound (DB itself is out-of-band).

## Rollback sketch

```text
# routing freeze only
git revert b457505ddd

# full PR including load-plan receipts (does NOT undo live DB)
git revert b457505ddd a905161eb0
```

Live orchestrator DB tags/loads are **not** undone by git revert — separate DB rollback packet required if needed.
