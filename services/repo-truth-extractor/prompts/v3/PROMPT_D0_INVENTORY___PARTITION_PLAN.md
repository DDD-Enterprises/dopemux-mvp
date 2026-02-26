OUTPUTS:
- DOC_INVENTORY.json
- DOC_PARTITIONS.json
- DOC_TODO_QUEUE.json

Goal: DOC_INVENTORY.json, DOC_PARTITIONS.json, DOC_TODO_QUEUE.json

Prompt:
- Scan docs/** (include archive dirs but tag them as archive).
- For each doc:
  - path, size, mtime, top headings, first 40 non-empty lines, token count estimate.
  - tag: ACTIVE vs ARCHIVE vs QUARANTINE based on path + in-doc markers.
- Create partitions:
  - core architecture
  - planes (pm/memory/orchestrator/mcp/hooks)
  - services (dope-memory, eventbus, dashboards, etc.)
  - task-packets + governance
  - research/audits
  - archives (split into manageable buckets)
- Output a queue of partitions with recommended run order.
```markdown

OUTPUTS:
	•	DOC_INVENTORY.json
	•	DOC_PARTITIONS.json
	•	DOC_TODO_QUEUE.json
```
