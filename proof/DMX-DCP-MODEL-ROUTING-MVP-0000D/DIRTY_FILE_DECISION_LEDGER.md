# DMX-DCP-MODEL-ROUTING-MVP-0000D — DIRTY_FILE_DECISION_LEDGER.md

**Branch**: `dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat`
**HEAD**: `438cb910c88c2164ab1eddf0183f5a65f1af7d32`
**Date**: 2026-06-09

## Tracked Modifications (Current Session)

| Path | Status | Classification | Red lane? | Reason | Recommended action |
|------|--------|----------------|-----------|--------|--------------------|
| `config/repo_hygiene/root_hygiene_policy.json` | M | `unknown` | No | New file in this session | Needs supervisor review |
| `services/dcp-readonly-facade/src/dcp_facade/tools.py` | M | `unknown` | No | New file in this session | Needs supervisor review |

## Untracked Files (Current Session)

| Path | Status | Classification | Red lane? | Reason | Recommended action |
|------|--------|----------------|-----------|--------|--------------------|
| `llm-plans/queue_drain_plan.md` | ?? | `stale_scratch` | No | Planning document | Review then delete or move to proof |
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000C.md` | ?? | `intended_routing_work` | No | This packet | KEEP |
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000D.md` | ?? | `intended_routing_work` | No | This packet | KEEP |
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000H.md` | ?? | `intended_routing_work` | No | This packet | KEEP |

## Red-Lane Files

| Path | Status | Classification | Red lane? | Reason | Recommended action |
|------|--------|----------------|-----------|--------|--------------------|
| `.github/workflows/gemini-review.yml` | Not modified in current diff | `red_lane_conflict` (from 0000B) | YES | Still present in worktree history | Must be reverted or justified before 0001 merge |

## Summary

**New tracked files since 0000B**: 2 (both `unknown` — need supervisor)
**New untracked files**: 4 (3 intended routing work, 1 stale scratch)
**Red-lane status**: `.github/workflows/gemini-review.yml` remains the primary red-lane conflict from 0000B

**Action Required Before 0001**:
1. Classify the two new tracked files (`root_hygiene_policy.json` and `dcp_facade/tools.py`)
2. Decide on `llm-plans/queue_drain_plan.md`
3. Resolve or document the `gemini-review.yml` red-lane conflict
