## PM-Pack Evidence Index

This PM-specific synthesis used only the PM workflow packs below.

## Leantime PM pack files used

| File | Used For |
| --- | --- |
| `reports/leantime-pm-workflow-pack/02-workflow-and-transition-analysis.md` | PM-pack evidence that workflow legality is mostly not enforced centrally and that direct mutation paths dominate. |
| `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md` | PM-pack evidence for absent next-action computation, advisory blocker semantics, and PM progress surfaces. |
| `reports/leantime-pm-workflow-pack/04-history-audit-and-chronicle.md` | PM-pack evidence for ticket history, audit, comments, notifications, and PM chronology. |
| `reports/leantime-pm-workflow-pack/05-integration-seams.md` | PM-pack evidence for JSON-RPC, legacy mutation surfaces, plugin hooks, and connector seams. |
| `reports/leantime-pm-workflow-pack/06-repo-local-authority-verdict.md` | Repo-local verdict that Leantime owns PM record state and only partially owns workflow constraints. |
| `reports/leantime-pm-workflow-pack/99-evidence-index.md` | Scope guard and negative-evidence search record. |

## Task Orchestrator PM pack files used

| File | Used For |
| --- | --- |
| `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md` | PM-pack evidence for explicit legality engine plus direct mutation bypass via `manage_items`. |
| `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md` | PM-pack evidence for dependency gates, blocker derivation, note gates, next-action computation, and role-progress signals. |
| `reports/task-orchestrator-pm-workflow-pack/04-audit-history-and-chronicle.md` | PM-pack evidence for `role_transitions`, mutable notes, and the audit-write reliability caveat. |
| `reports/task-orchestrator-pm-workflow-pack/05-runtime-variants-and-local-split-brain-risks.md` | PM-pack evidence for internal split-brain risks across runtime variants and write paths. |
| `reports/task-orchestrator-pm-workflow-pack/06-integration-seams.md` | PM-pack evidence for MCP, config seams, transport seams, and lack of non-MCP ingress. |
| `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md` | Repo-local verdict that Task Orchestrator owns workflow persistence and transition-path legality, but not universal legality or decisions. |
| `reports/task-orchestrator-pm-workflow-pack/99-evidence-index.md` | Scope guard and negative-evidence search record. |

## PM-Pack-Specific Interpretation Note

Compared with the repo-truth-pack synthesis, the PM-pack evidence adds a stronger implementation caveat:

- `Task Orchestrator` is the stronger workflow authority, but only on sanctioned transition paths.
- `Leantime` is the PM record authority, but its own mutation paths do not provide a universal workflow-law boundary.
