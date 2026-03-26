## PM-Pack Authority Split Verdict

Scope note: this verdict is based on the PM workflow packs only.

## 1. PM-facing record state

`Leantime` is the clearest authority.

Its PM pack explicitly marks the repo authoritative for current PM record state across projects, tickets, milestones, subtasks, sprints, timesheets, comments, and related membership links, and it identifies multiple local mutation paths and API ingress points that already own those records. Task Orchestrator’s PM pack marks authority over its own MCP/workflow persistence model, not over the human-facing PM record. Evidence: `reports/leantime-pm-workflow-pack/06-repo-local-authority-verdict.md`, `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md`.

## 2. Workflow legality

`Task Orchestrator` is the best workflow-law authority, but only conditionally.

Leantime’s PM pack says formal workflow legality is mostly not enforced centrally. Task Orchestrator’s PM pack says a real legality engine exists, but only for callers that use `advance_item` and `complete_tree`. Because `manage_items` can still mutate `role` directly, the PM-pack verdict is not "globally authoritative out of the box"; it is "authoritative on the sanctioned transition paths." Evidence: `reports/leantime-pm-workflow-pack/02-workflow-and-transition-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md`.

## 3. Blockers / dependencies

`Task Orchestrator` is the authority.

Leantime models blockers as status/display/hierarchy artifacts and does not enforce them as transition gates. Task Orchestrator computes dependency legality, blocked sets, and unblock readiness on its workflow paths. The PM packs support treating Leantime blocker state as advisory and Task Orchestrator blocker state as canonical. Evidence: `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`.

## 4. Next-action computation

`Task Orchestrator` is the only evidenced authority.

Leantime’s PM pack explicitly records no evidence of next-action computation. Task Orchestrator’s PM pack explicitly records `get_next_item` and `get_next_status` as derived next-step surfaces. This is the cleanest category in the PM-pack comparison. Evidence: `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`.

## 5. Decisions / progress

This remains split, and canonical decision ownership is unresolved.

Leantime shows richer PM progress and decision-like artifacts, but its PM pack found no dedicated decision register. Task Orchestrator shows role-progress and workflow readiness, but its PM pack also found no explicit decision entity or table. The most defensible PM-pack reading is:

- PM-visible progress authority: `Leantime`
- Workflow-execution progress authority: `Task Orchestrator`
- Canonical decision authority: `Unresolved`

Evidence: `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/leantime-pm-workflow-pack/06-repo-local-authority-verdict.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`, `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md`.

## 6. Chronicle / history / audit

This is a split authority domain.

Leantime owns the broader PM chronicle through ticket history, audit, comments, and notifications. Task Orchestrator owns the dedicated workflow transition history through `role_transitions`, but its PM pack also flags that transition-audit persistence is not checked for success, so this chronicle is narrower and slightly softer than it first appears. Evidence: `reports/leantime-pm-workflow-pack/04-history-audit-and-chronicle.md`, `reports/task-orchestrator-pm-workflow-pack/04-audit-history-and-chronicle.md`.

## PM-Pack Summary Verdict

- PM-facing record state: `Leantime`
- Workflow legality: `Task Orchestrator`, but only on sanctioned transition paths
- Blockers/dependencies: `Task Orchestrator`
- Next-action computation: `Task Orchestrator`
- Decisions/progress: `Split`, with canonical decisions `Unresolved`
- Chronicle/history/audit: `Split`

## Strongest PM-Pack Reading

The PM-pack evidence supports a guarded dual-authority model:

- `Leantime` is the canonical PM record.
- `Task Orchestrator` is the canonical workflow engine and action recommender.
- Integration policy must forbid or reconcile bypass paths, especially direct `manage_items` role mutation in Task Orchestrator and direct status/state mutation paths in Leantime, or the intended authority split will not hold in practice.
