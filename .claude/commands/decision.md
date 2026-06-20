Log an architectural or implementation **decision** to **ConPort** (Memory Trinity plane 1 — canonical writer).

Call: `mcp__conport__log_decision`

```json
{
  "workspace_id": "<repo-root>",
  "summary": "<one-line decision>",
  "rationale": "<why>",
  "tags": ["project:<name>", "slice:<name>", "decision"]
}
```

Mirror receipt: dope-memory chronicle mirrors ConPort writes automatically via `memory_writers` when orchestrator path is active.

> Token thrift: prefer `search_decisions_fts` with `limit` 3–5 before loading full context.