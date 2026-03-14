OUTPUTS:
- RISK_REGISTER_TOP20.md

Goal: RISK_REGISTER_TOP20.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase B (boundary) or Phase E (execution) or Phase Q (QA) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase B: BOUNDARY_BYPASS_RISKS — bypass vectors with severity ratings
- Phase E: EXEC_RISK_FACTS — execution-layer risk locations
- Phase Q: QA_MISSING_ARTIFACTS — evidence gaps affecting risk ranking
- Phase X: FEATURE_DEP_GRAPH, FEATURE_SURFACE — feature coupling and dependency risks

TASK:
Produce top-20 risk register.

MUST INCLUDE:
- Determinism/idempotency/concurrency risks
- Boundary bypass risks
- Severity ranking with evidence
- Minimal mechanical bounding mechanisms

RULES:
- Cite every risk item.
- No large refactor recommendations.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```
