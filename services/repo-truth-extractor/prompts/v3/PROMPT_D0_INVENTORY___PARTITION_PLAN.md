OUTPUTS:
- DOC_INVENTORY.json
- DOC_PARTITIONS.json
- DOC_TODO_QUEUE.json

Hard rules:
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited line_range MUST use the line numbers shown in the provided excerpt.
- Every items[] entry MUST include id, path, and line_range.
- Every evidence object MUST include repo-relative path, integer line_range, and exact excerpt.
- If a value cannot be grounded from the provided excerpt, return valid JSON with UNKNOWN or fail-closed placeholders; never invent line numbers.

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
