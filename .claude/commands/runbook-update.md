Append steps/lessons to `docs/runbooks/<topic>.md` + log **ConPort** progress/decision.

1. Update the runbook markdown under `docs/runbooks/`.
2. `mcp__conport__log_decision` or `mcp__conport__log_progress` referencing the runbook path.

> Token thrift: prefer ConPort summaries/search before full context: `search_content` has no `limit` (read only the top 3–5 results); `get_decisions` and `get_progress` accept `limit`.
