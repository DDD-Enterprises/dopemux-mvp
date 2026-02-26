Goal: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce memory implementation truth for current system behavior.

MUST INCLUDE:
- Stores/adapters (sqlite/postgres/other)
- Schema objects from DOPE_MEMORY_SCHEMAS.json
- Write paths from DOPE_MEMORY_DB_WRITES.json
- Retention/TTL enforcement points
- Replay/re-derive surfaces (if present)
- Control-plane dependencies (env vars, compose wiring, home DBs)

FORMAT:
1) IMPLEMENTED (CODE evidence)
2) PLANNED (DOC evidence)
3) GAPS/CONFLICTS (both sides cited)
4) Minimal verification command suggestions

RULES:
- Cite statements for tables/triggers/enforcement points.
- If docs conflict, use DOC_SUPERSESSION then recency tie-breaker.

```markdown

OUTPUTS:
	•	DOPE_MEMORY_DB_WRITES.json
	•	DOPE_MEMORY_SCHEMAS.json
```
