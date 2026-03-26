## Split-Brain Risks

Source boundary: merged from the repo truth packs and PM workflow packs.

### 1. Illegal Leantime transitions can bypass Task Orchestrator workflow law

Severity: High

Leantime permits unrestricted ticket status changes, while Task Orchestrator rejects illegal forward moves when dependencies or note gates are unsatisfied. If users or integrations write status directly in Leantime, the PM record can claim progress that Task Orchestrator would have blocked. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_WORKFLOW_AND_GATES.md`, `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md`.

### 2. Dual task stores can create competing notions of "current truth"

Severity: High

Leantime persists PM entities in its own domain tables, and Task Orchestrator persists `work_items`, `notes`, `dependencies`, and `role_transitions`. Without a strict ownership model, both systems can appear canonical for the same unit of work. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/task-orchestratorrepo-truth-pack/DATA_MODEL.md`.

### 3. Task Orchestrator has an internal legality bypass

Severity: High

The PM-pack scan shows a real legality engine on `advance_item` and `complete_tree`, but also a direct `manage_items` role-update path that bypasses that legality model. That means Task Orchestrator can split against itself unless integrations lock down which write surfaces are allowed. Evidence: `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md`, `reports/task-orchestrator-pm-workflow-pack/05-runtime-variants-and-local-split-brain-risks.md`.

### 4. Dependency semantics are not compatible across the two systems

Severity: High

Leantime's `dependingTicketId` is documented as parent-child/subtask linkage, not blocker semantics, and its relationship enum only defines `Collaborator`. Task Orchestrator uses explicit dependency edge types plus `unblockAt` thresholds. Mapping one directly onto the other would silently corrupt meaning. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/leantime-repo-truth-pack/LEANTIME_WORKFLOW_AND_GATES.md`, `reports/task-orchestratorrepo-truth-pack/DATA_MODEL.md`.

### 5. Next-action recommendations can drift from PM state

Severity: High

Task Orchestrator computes next action from workflow legality, dependencies, and gates. Leantime exposes PM state and reporting but no equivalent legality engine. If synchronization lags or Leantime is edited directly, the "next action" and the visible PM state can diverge. Evidence: `reports/leantime-repo-truth-pack/INTEGRATION_NOTES.md`, `reports/task-orchestratorrepo-truth-pack/MCP_TOOL_MANIFEST.json`, `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md`.

### 6. Progress can mean different things in each system

Severity: Medium

Leantime progress includes reports, milestone progress, project summaries, goals, and PM-facing tracking. Task Orchestrator progress is role advancement inside a work-item graph. These are related but not identical concepts, so naive synchronization can create false mismatches. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_KNOWLEDGE_AND_REPORTING_SURFACES.md`, `reports/task-orchestratorrepo-truth-pack/EXECUTIVE_SUMMARY.md`, `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md`.

### 7. History becomes fragmented across PM audit and workflow audit ledgers

Severity: Medium

Leantime owns PM-entity history surfaces such as ticket history and audit-like activity. Task Orchestrator separately records workflow transitions. If no cross-link exists, investigators must reconstruct one timeline from two ledgers with different semantics. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/leantime-repo-truth-pack/LEANTIME_KNOWLEDGE_AND_REPORTING_SURFACES.md`, `reports/task-orchestratorrepo-truth-pack/DATA_MODEL.md`.

### 8. Task Orchestrator has an internal runtime split risk

Severity: Medium

Its integration notes describe two incompatible deployable modules, `clockwork` and `current`, with different tool sets and transports. A cross-repo integration that targets the wrong module can create its own split-brain even before Leantime is involved. Evidence: `reports/task-orchestratorrepo-truth-pack/INTEGRATION_NOTES.md`.

### 9. Decision authority is not fully closed inside this pair of repos

Severity: Medium

Leantime contains decision-bearing artifacts, but its own PM-plane mapping recommends promotion of durable decisions and rationale to ConPort. Task Orchestrator shows workflow context and notes, but not a separate durable decision canon. If the integration tries to force a single decision authority solely out of these two repos, it will over-claim beyond the evidence. Evidence: `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md`, `reports/task-orchestratorrepo-truth-pack/ARCHITECTURE_AND_INTENDED_USES.md`.

## Risk Pattern Summary

The dominant split-brain pattern is simple: Leantime is flexible where Task Orchestrator is strict, and Task Orchestrator itself has bypass paths if callers use the wrong tool path. Any design that does not explicitly constrain mutation surfaces will drift.
