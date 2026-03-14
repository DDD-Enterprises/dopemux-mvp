## PM-Pack Split-Brain Risks

Source boundary: PM workflow packs only.

## 1. Leantime has multiple direct mutation paths with inconsistent legality

Severity: High

Its PM pack shows direct status/state mutation APIs and only localized guards. That means one path can enforce a rule while another bypasses it, producing internal Leantime drift before any cross-repo sync even happens. Evidence: `reports/leantime-pm-workflow-pack/02-workflow-and-transition-analysis.md`, `reports/leantime-pm-workflow-pack/06-repo-local-authority-verdict.md`.

## 2. Task Orchestrator has a legality bypass inside its own MCP surface

Severity: High

Its PM pack shows a real legality engine on `advance_item` and `complete_tree`, but also shows that `manage_items` can write `role` directly. That creates local split-brain between "validated workflow transitions" and "direct state mutation." Evidence: `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/05-runtime-variants-and-local-split-brain-risks.md`, `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md`.

## 3. Leantime blocker semantics are advisory while Task Orchestrator blocker semantics are legal

Severity: High

Leantime exposes blocked/dependency concepts without mandatory gate enforcement. Task Orchestrator uses blockers to compute readiness and to validate transition paths. If these are merged naively, users will see two incompatible meanings of "blocked." Evidence: `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`.

## 4. Next-action truth exists in one system only

Severity: High

Leantime’s PM pack found no next-action engine. Task Orchestrator’s PM pack found a dedicated derived/advisory next-action engine. If Leantime UI or integrations improvise their own next step from PM fields, they will create a second competing recommendation layer. Evidence: `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`.

## 5. Progress is semantically split between PM analytics and workflow progression

Severity: Medium

Leantime computes project, milestone, sprint, and checklist-style progress. Task Orchestrator computes progression position, blocked readiness, and overview role counts. These are not identical signals, so "percent complete" and "ready to advance" can diverge without either system being wrong. Evidence: `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`.

## 6. Chronicle is split across broad PM history and narrow workflow history

Severity: Medium

Leantime has ticket history, audit, comments, notifications, and read markers. Task Orchestrator has `role_transitions` plus mutable notes. Investigators can end up with two partial narratives unless records are explicitly cross-linked. Evidence: `reports/leantime-pm-workflow-pack/04-history-audit-and-chronicle.md`, `reports/task-orchestrator-pm-workflow-pack/04-audit-history-and-chronicle.md`.

## 7. Task Orchestrator has internal runtime split-brain risk independent of Leantime

Severity: Medium

Its PM pack documents parallel v2 and v3 modules, multiple Docker targets, multiple compose services, schema-management variants, and duplicate internal write paths. An integration can accidentally target the wrong runtime or the wrong write path and produce inconsistent behavior from one repo alone. Evidence: `reports/task-orchestrator-pm-workflow-pack/05-runtime-variants-and-local-split-brain-risks.md`.

## 8. Canonical decisions are not cleanly owned by either PM pack

Severity: Medium

Leantime stores decision-like content without a dedicated decision register. Task Orchestrator stores workflow context without an explicit decision object. If the integrated design assumes one system is the decision authority, it will outrun the PM-pack evidence. Evidence: `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md`, `reports/task-orchestrator-pm-workflow-pack/07-repo-local-authority-verdict.md`.

## PM-Pack Risk Summary

The biggest PM-pack-specific lesson is that both systems have bypass paths. The intended authority split is sound, but it is not self-enforcing unless integration policy narrows which mutation surfaces are allowed.
