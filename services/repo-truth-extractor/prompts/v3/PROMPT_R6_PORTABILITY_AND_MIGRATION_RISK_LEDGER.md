OUTPUTS:
- PORTABILITY_AND_MIGRATION_RISK_LEDGER.md

Goal: PORTABILITY_AND_MIGRATION_RISK_LEDGER.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase G (governance) or Phase W (workflow) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase G: GOV_POLICIES, GOV_CI_GATES — governance scope, enforcement gates
- Phase W: WORKFLOW_STATE_COUPLING — state dependencies affecting portability

TASK:
Produce portability and migration risk ledger.

MUST INCLUDE:
- Home-only dependencies
- Required env vars
- MCP dependencies vs hooks opportunities
- Evidence-based "what breaks if moved to hooks"

RULES:
- Cite every risk.
- No broad refactor proposals.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```
