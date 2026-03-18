OUTPUTS:
- CONFLICT_LEDGER.md

Goal: CONFLICT_LEDGER.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason from normalized A/H/D/C artifacts (required). If Phase Q (QA) or Phase G (governance) normalized artifacts are present in input, incorporate them as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase Q: QA_MISSING_ARTIFACTS, QA_NORM_DRIFT_REPORT, PIPELINE_DOCTOR_REPORT — pipeline health, missing evidence, drift
- Phase G: GOV_POLICIES — governance authority for conflict resolution hierarchy

TASK:
Produce conflict ledger across docs/code/control planes.

MUST INCLUDE:
- doc claim vs code truth
- doc vs doc conflicts
- authority decisions using evidence hierarchy

RULES:
- Use DOC_SUPERSESSION first, then recency tie-breaker for doc-vs-doc only.
- Never override code reality with docs.
- Cite both sides for each conflict.

```markdown

OUTPUTS:
	•	TRUTH_MAP.json
```
