## Authority Split Verdict

Scope note: this verdict is constrained to the two repo truth packs now present in `reports/`. The restored PM workflow packs were not used as primary evidence so the synthesis stays within the original source boundary.

### 1. PM-facing record state

`Leantime` is the most defensible authority.

Its truth pack explicitly frames Leantime as the PM system and source of truth for tickets, projects, sprints, milestones, users, timesheets, files, comments, clients, and related operational records. Task Orchestrator, by contrast, is evidenced as a persistent work-item graph for AI workflow management, not as the human-facing PM system of record. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/leantime-repo-truth-pack/INTEGRATION_NOTES.md`, `reports/task-orchestratorrepo-truth-pack/EXECUTIVE_SUMMARY.md`.

### 2. Workflow legality

`Task Orchestrator` is the clear authority.

Leantime implements no enforceable ticket state machine and allows unrestricted status transitions. Task Orchestrator implements deterministic trigger-based transitions, validation, and explicit rejection paths. If a single system must decide whether a transition is legal, the evidence strongly favors Task Orchestrator. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_WORKFLOW_AND_GATES.md`, `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md`.

### 3. Blockers / dependencies

`Task Orchestrator` is the clear authority.

Leantime has no blocker enforcement mechanism, no blocker relationship enum, and its `dependingTicketId` field is explicitly described as parent-child linkage rather than dependency legality. Task Orchestrator has first-class dependency records and uses them to gate advancement. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/leantime-repo-truth-pack/LEANTIME_WORKFLOW_AND_GATES.md`, `reports/task-orchestratorrepo-truth-pack/DATA_MODEL.md`, `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md`.

### 4. Next-action computation

`Task Orchestrator` is the clear authority.

Leantime offers query and reporting APIs, but the pack does not evidence legality-aware next-step computation. Task Orchestrator exposes dedicated next-item, blocked-item, next-status, and context surfaces that derive recommendations from workflow state, dependencies, and gates. Evidence: `reports/leantime-repo-truth-pack/INTEGRATION_NOTES.md`, `reports/task-orchestratorrepo-truth-pack/EXECUTIVE_SUMMARY.md`, `reports/task-orchestratorrepo-truth-pack/MCP_TOOL_MANIFEST.json`.

### 5. Decisions / progress

This domain is split, with one unresolved boundary.

`Leantime` is best supported as the authority for PM-visible decision-bearing artifacts and PM-visible progress surfaces: goals, wiki, retros, risks, approvals, reports, milestone progress, and acceptance criteria. `Task Orchestrator` is best supported as the authority for execution progress inside its own workflow graph: role progression, gate satisfaction, cascades, and unblock state. The unresolved boundary is durable decision canon beyond PM presentation, because the Leantime pack itself points that responsibility toward ConPort rather than either Leantime or Task Orchestrator. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/leantime-repo-truth-pack/LEANTIME_KNOWLEDGE_AND_REPORTING_SURFACES.md`, `reports/task-orchestratorrepo-truth-pack/EXECUTIVE_SUMMARY.md`, `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md`.

### 6. Chronicle / history / audit

This domain is also split.

`Leantime` is the best-supported PM chronicle for PM entities. `Task Orchestrator` is the best-supported workflow audit log for legality decisions and role transitions. The evidence does not support collapsing these into a single natural owner without loss of meaning, because each ledger records different classes of fact. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/leantime-repo-truth-pack/LEANTIME_KNOWLEDGE_AND_REPORTING_SURFACES.md`, `reports/task-orchestratorrepo-truth-pack/DATA_MODEL.md`, `reports/task-orchestratorrepo-truth-pack/ARCHITECTURE_AND_INTENDED_USES.md`.

## Verdict Summary

- PM-facing record state: `Leantime`
- Workflow legality: `Task Orchestrator`
- Blockers/dependencies: `Task Orchestrator`
- Next-action computation: `Task Orchestrator`
- Decisions/progress: `Split`, with durable decision canon `Unresolved` inside this two-repo comparison
- Chronicle/history/audit: `Split`

## Most Defensible Overall Model

The strongest evidence-backed model is not "pick one system for everything." It is a deliberate dual-authority design:

- `Leantime` is the canonical PM record and PM-facing narrative surface.
- `Task Orchestrator` is the canonical workflow-law and action-selection engine.
- Any design that asks Leantime to enforce workflow legality, or asks Task Orchestrator to become the PM system of record, is weaker than what the extracted evidence supports.
