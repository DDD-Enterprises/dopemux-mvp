# Next Action — GB-DMX-DCP-QUEUE-REPLAN-001

## DCP_QUEUE_REPLAN_RESULT

```yaml
origin_main_sha: 724a25fa01c77f7f1fd6ccf8a78da09f082e0ded
phase1_status: COMPLETE (#908, #909, #906, #923, #915, #920 merged; lane engine + provenance runtime on main)
open_dcp_prs:
  - 931  # only open DCP PR
recommended_next_active_pr: 931
recommended_order:
  - 931
  - "(conditional) fresh tooling-design PR replacing closed #878 if 103–115 series continues"
close_or_supersede_recommendations:
  - "#878: remain CLOSED; refresh packets on new branch if tooling design still needed"
  - "#873: merged evidence archive — no action"
  - "#885: merged — no action"
  - "Evaluate #931 against merged #926 before merge to avoid duplicate contract trees"
blockers:
  - "#931 STALE_BASE (6 commits behind origin/main)"
  - "#931 semantic overlap with merged #926"
  - "Tooling packets 103–115 not on main"
unknowns:
  - "#878 close rationale detail"
  - "Operator priority: #931 OpenClaw vs tooling design refresh"
artifact_paths:
  - audit_inputs/dcp_queue_replan/DCP_OPEN_PR_LEDGER.md
  - audit_inputs/dcp_queue_replan/DCP_OPEN_PR_LEDGER.json
  - audit_inputs/dcp_queue_replan/COMMAND_LOG.md
  - audit_inputs/dcp_queue_replan/NEXT_ACTION.md
```

## NEXT_OPERATOR_ACTION

**Refresh #878 task packets before merge.**

### Rationale (live queue diverges from seed)

Seed assumed #878/#885/#873 were open contenders. Live state:

- **#931** is the only open DCP PR and the practical merge candidate after rebase.
- **#878** is already **CLOSED unmerged** with stale/conflicting base and 3 unresolved threads — it cannot be made current without a **full packet refresh on a new branch**.
- Allowed outcomes did not include #931; this action addresses the highest-risk **DCP tooling gap** (103–115 packets never landed) while #931 proceeds in parallel.

### Immediate sub-steps (operator, not executed here)

1. Rebase #931 onto `724a25fa` and resolve `contracts/` vs `docs/03-reference/dcp/openclaw-routing/` duplication.
2. If tooling series continues: extract #878 design pack, refresh `DMX-DCP-TOOLING-{103..115}` against post-Phase-1 main, open **new** PR (do not resurrect #878 branch).