OUTPUTS:
- WORKFLOWS_TRUTH_GRAPH.md

Goal: WORKFLOWS_TRUTH_GRAPH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase W (workflow) or Phase E (execution) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase W: WORKFLOW_CATALOG, WORKFLOW_IO_MAP, WORKFLOW_COORDINATION_SURFACE, WORKFLOW_FAILURE_RECOVERY, WORKFLOW_STATE_COUPLING — runbook steps, coordination, failure scenarios
- Phase E: EXEC_STARTUP_GRAPH, EXEC_RUNTIME_MODES — startup sequences, runtime modes

TASK:
Produce workflow truth graph.

MUST INCLUDE:
- Bootstrap flows (tmux, compose, scripts)
- Multi-service workflows with order/dependencies
- Inputs/outputs/artifacts where explicit
- Instruction-file-driven workflow steps

OUTPUT:
- Workflow list (W1..Wn) with literal steps + citations
- Services involved per workflow
- UNKNOWN markers where evidence is missing

RULES:
- No inferred steps.
- Use WORKFLOW_RUNNER_SURFACE + HOME_TMUX_WORKFLOW_SURFACE + compose graph evidence.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```
