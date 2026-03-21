## Evidence Index

This merged synthesis used both the repo truth packs and the PM workflow packs below.

## Leantime truth-pack files used

| File | Used For |
| --- | --- |
| `reports/leantime-repo-truth-pack/EXECUTIVE_SUMMARY.md` | High-level claim that Leantime is the PM data store and does not enforce workflow rules. |
| `reports/leantime-repo-truth-pack/INTEGRATION_NOTES.md` | Explicit authority guidance: keep PM entities authoritative in Leantime; Task Orchestrator should own workflow rules. |
| `reports/leantime-repo-truth-pack/LEANTIME_PM_PLANE_MAPPING.md` | Detailed authority boundaries for operational PM state, durable decision-bearing artifacts, blocker limitations, and audit ownership. |
| `reports/leantime-repo-truth-pack/LEANTIME_WORKFLOW_AND_GATES.md` | Proof that ticket transitions are unrestricted, blocker semantics are absent, and sprint/milestone gating is not enforced. |
| `reports/leantime-repo-truth-pack/LEANTIME_KNOWLEDGE_AND_REPORTING_SURFACES.md` | Evidence for PM-visible progress, decision-bearing artifacts, and history/reporting surfaces. |
| `reports/leantime-repo-truth-pack/CALLABLE_SURFACE_MANIFEST.json` | Verification of the breadth of PM-facing read/write surfaces. |
| `reports/leantime-repo-truth-pack/APPENDIX_C_OPEN_QUESTIONS.md` | Boundaries on unresolved features such as approvals and MCP registration. |

## Task Orchestrator truth-pack files used

| File | Used For |
| --- | --- |
| `reports/task-orchestratorrepo-truth-pack/EXECUTIVE_SUMMARY.md` | High-level claim that Task Orchestrator is a persistent work-item graph with server-enforced dependency gates and workflow transitions. |
| `reports/task-orchestratorrepo-truth-pack/DATA_MODEL.md` | Proof of `work_items`, `dependencies`, `notes`, `role_transitions`, optimistic versioning, and dependency schema. |
| `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md` | Proof of the legal transition model, dependency gating, note gates, cascades, and workflow audit behavior. |
| `reports/task-orchestratorrepo-truth-pack/ARCHITECTURE_AND_INTENDED_USES.md` | Architectural intent showing Task Orchestrator as workflow enforcement and session/action engine rather than PM record system. |
| `reports/task-orchestratorrepo-truth-pack/MCP_TOOL_MANIFEST.json` | Verification of next-action and dependency-related tool surfaces. |
| `reports/task-orchestratorrepo-truth-pack/INTEGRATION_NOTES.md` | Evidence of internal v2/v3 runtime split risk and routing semantics. |
| `reports/task-orchestratorrepo-truth-pack/APPENDIX_C_OPEN_QUESTIONS.md` | Limits on unresolved transport/auth and response-schema behavior. |

## PM workflow-pack files used

| File | Used For |
| --- | --- |
| `reports/leantime-pm-workflow-pack/02-workflow-and-transition-analysis.md` | PM-pack evidence that Leantime workflow legality is mostly not enforced centrally. |
| `reports/leantime-pm-workflow-pack/03-action-blocker-progress-analysis.md` | PM-pack evidence for advisory blocker semantics and absent next-action computation in Leantime. |
| `reports/leantime-pm-workflow-pack/04-history-audit-and-chronicle.md` | PM-pack evidence for Leantime’s broader PM chronicle. |
| `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md` | PM-pack evidence that Task Orchestrator’s legality engine exists but can be bypassed through direct role writes. |
| `reports/task-orchestrator-pm-workflow-pack/03-gates-actions-and-progress.md` | PM-pack evidence for blockers, next-action derivation, and progress semantics in Task Orchestrator. |
| `reports/task-orchestrator-pm-workflow-pack/04-audit-history-and-chronicle.md` | PM-pack evidence for workflow audit scope and audit-write reliability caveat. |
| `reports/task-orchestrator-pm-workflow-pack/05-runtime-variants-and-local-split-brain-risks.md` | PM-pack evidence for internal runtime and write-path split-brain risks. |

## Files restored and used as secondary constraint evidence

The following directories were restored into `reports/` and are part of the merged canonical synthesis:

- `reports/leantime-pm-workflow-pack/`
- `reports/task-orchestrator-pm-workflow-pack/`

## Provenance Note

The four pack directories were restored into this checkout from `remotes/upstream/codex/all-work-bundle-20260311`, because the current `main` worktree only contained placeholder directories for the truth packs.
