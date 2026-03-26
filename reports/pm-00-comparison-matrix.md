## PM-Pack Comparison Matrix

Source boundary: this matrix uses the PM workflow packs only:

- `reports/leantime-pm-workflow-pack/*`
- `reports/task-orchestrator-pm-workflow-pack/*`

| Domain | Leantime PM-Pack Finding | Task Orchestrator PM-Pack Finding | Overlap | Conflict | PM-Pack Canonical Verdict | PM-Pack Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PM-facing record state | Authoritative for persisted PM record state: projects, tickets, milestones, subtasks, sprints, timesheets, comments, membership links, and major mutation ingress points. | Authoritative for its own SQLite `WorkItem`, `Note`, `Dependency`, and `RoleTransition` records, but these are repo-local MCP/workflow records. | Both persist work-related state. | Dual stores can both look like "the task database." | `Leantime` | `reports/leantime-pm-workflow-pack/06-repo-local-authority-verdict.md`, `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md` |
| Workflow legality | Mostly not enforced centrally; direct mutation APIs dominate; localized guards exist but are inconsistent across write paths. | Explicit trigger-based legality engine exists, but only authoritative on transition-path tools; direct `manage_items` role writes bypass it. | Both can mutate status/role. | Neither repo gives a truly universal write-boundary legality guarantee today. | `Task Orchestrator`, but only if integrations constrain writes to transition paths | `reports/leantime-pm-workflow-pack/02-workflow-and-transition-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md` |
| Blockers / dependencies | Partially implemented as status/display/hierarchy; not enforced as mandatory gates. | Authoritative on transition recommendation and advance paths; partial globally because bypass writes exist. | Both expose blocker/dependency concepts. | Leantime blocker semantics are advisory/display; Task Orchestrator semantics are legal/gating semantics. | `Task Orchestrator` | `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md` |
| Next-action computation | Absent / no evidence found. | Derived/advisory engine implemented via `get_next_item` and `get_next_status`. | Both can expose current state to users. | Only one repo computes next action at all. | `Task Orchestrator` | `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`, `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md` |
| Decisions / progress | Strong PM progress surfaces exist; explicit decision register is absent; decision-like content lives in canvases and comments. | Partially authoritative for role-progress; explicit decision persistence is absent. | Both contain progress-like signals; neither shows a first-class decision ledger. | "Decision authority" cannot be cleanly assigned from PM-pack evidence alone. | `Split for progress`; `Unresolved` for canonical decisions | `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/leantime-pm-workflow-pack/06-repo-local-authority-verdict.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`, `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md` |
| Chronicle / history / audit | Richer PM chronicle: ticket history, audit, comments, notifications, read markers. | Dedicated workflow transition audit exists, but audit persistence success is not checked; notes are mutable artifacts, not immutable chronicle. | Both keep history. | Leantime has broader PM chronology; Task Orchestrator has narrower workflow chronology with a reliability caveat. | `Split`: Leantime for PM chronicle, Task Orchestrator for workflow transition history | `reports/leantime-pm-workflow-pack/04-history-audit-and-chronicle.md`, `reports/task-orchestrator-pm-workflow-pack/04-audit-history-and-chronicle.md` |

## PM-Pack Takeaway

The PM packs support a stricter and slightly more cautionary conclusion than the repo-truth-pack set:

- `Leantime` is clearly the PM record authority.
- `Task Orchestrator` is the stronger workflow-law and next-action engine.
- But `Task Orchestrator` is not globally authoritative for legality until direct role-mutation bypasses are closed or forbidden by integration policy.
