# GAP_AND_DRIFT_REPORT — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

## Gaps (action required)

| ID | Title | Severity |
| --- | --- | --- |
| GAP-MAIN-001 | All Cockpit pack remediation work is missing from `origin/main` | blocking_for_design_pickup |
| GAP-MAIN-002 | `task-packets/generated/` directory does not exist on main | informational |
| GAP-MAIN-003 | No proof tree exists on main for the cockpit pack series | blocking_for_design_pickup |
| GAP-PACK-001 | PR 572 stack consolidation artifact does not audit PR 573 | blocking_for_design_pickup |
| GAP-PACK-002 | Settings/Admin per-row tier mapping residual risk accepted but not disposed | needs_ledger_decision |
| GAP-PACK-003 | Remote-mutation policy is absent and explicitly deferred per PR 572 | needs_ledger_decision |
| GAP-PACK-004 | Inventory artifact still records prior upstream `current_head` and aggregate-only precision risks | needs_ledger_decision |
| GAP-PACK-005 | `TP-DMX-COCKPIT-MERGE-EXECUTE-001` referenced but not authored | blocking_for_design_pickup |
| GAP-PACK-006 | No authored TP JSONs on pack for `cockpit-command-palette`, `cockpit-ia-reconcile`, `cockpit-pack-remediation`, `cockpit-safe-actions` `out/*` trees | informational |

## Drift items (record-only)

| ID | Title | Implication |
| --- | --- | --- |
| DRIFT-001 | Pack diverges from main by 18/9 commits and 196 files | any pack-to-main consolidation has a wide surface beyond the four merged feature PRs |
| DRIFT-002 | Cockpit PR stack base is `pack/cockpit-pack-remediate-006-ia`, not `main` | main can only receive this work via an operator-initiated consolidation packet |
| DRIFT-003 | Open PR 573 modifies cockpit runtime surface unaudited by PR 572 | if PR 572 is the only consolidation gate, PR 573 lands unaudited |
| DRIFT-004 | Non-Cockpit open PRs (#582 dependabot pip, #583 dependabot uv, #584 MCP review follow-ups) target main but do not touch Cockpit governance rows | do not let dependency churn or MCP review confound the Cockpit consolidation timeline |

## Non-actions

- no PR merges performed
- no PR retargets performed
- no PR edits performed
- no PR closes performed
- no rebases performed
- no force pushes performed
- no Claude Design upload performed
- no T4 remote mutation performed
- no canonical writes performed
- no runtime action execution performed
- no runtime reclassification performed

## Recommended follow-up sequence

See `DESIGN_PICKUP_PLAN.md` — gap closures are sequenced there.
