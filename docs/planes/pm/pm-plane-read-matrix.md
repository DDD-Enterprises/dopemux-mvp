---
id: pm-plane-read-matrix
title: PM Plane Read Matrix
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Reference matrix for normalized PM-plane tool reads, canonical sources, supporting sources, normalization, and provenance.
---
# PM Plane Read Matrix

| tool | canonical_source | supporting_sources | normalization_required | provenance_required | notes |
|---|---|---|---|---|---|
| `pm_get_project_context` | `ConPort` | `Leantime`, `dope-memory` | `yes` | `yes` | Durable context envelope with source-plane markers. |
| `pm_get_priority_queue` | `Task Orchestrator` | `Leantime` | `yes` | `yes` | Workflow authority determines ordering; Leantime only reflects PM record IDs. |
| `pm_get_blockers` | `Task Orchestrator` | `ConPort` | `yes` | `yes` | Blockers remain workflow truth even when supported by decision/context records. |
| `pm_get_workflow_state` | `Task Orchestrator` | `Leantime` | `yes` | `yes` | Response must separate workflow legality from PM-facing status fields. |
| `pm_update_work_item` | `Leantime` | `ConPort` | `request and response` | `yes` | Write tool. Read-back comes from Leantime plus any linked durable context. |
| `pm_transition_work_item` | `Task Orchestrator` | `Leantime`, `dope-memory` | `request and response` | `yes` | Write tool. Must expose workflow authority result plus any reflection receipts. |
| `pm_get_sprint_snapshot` | `Leantime` | `ConPort` | `yes` | `yes` | PM operational sprint snapshot with optional context attachments. |
| `pm_get_decision_context` | `ConPort` | `dope-memory` | `yes` | `yes` | Decision records plus linked chronicle references. |
| `pm_log_progress` | `ConPort` | `Leantime`, `dope-memory` | `request and response` | `yes` | Write tool. Read-back comes from ConPort progress plus mirror receipts. |
| `pm_get_work_chronicle` | `dope-memory` | `ConPort`, `Leantime` | `yes` | `yes` | Timeline view must keep chronicle truth distinct from referenced PM/context records. |
| `pm_search_project_knowledge` | `dope-context` | `ConPort`, `dope-memory`, `Leantime` | `yes` | `yes` | Search results must preserve retrieval provenance and source-plane identity. |
| `pm_get_technical_context` | `Serena` | `ConPort`, `dope-context` | `yes` | `yes` | Technical context remains technical even when linked into PM work. |

## Notes

- Multi-plane reads are allowed, but only one `canonical_source` may own the result's primary object class.
- For write tools, this matrix records the canonical source for write receipts and read-back after mutation.
