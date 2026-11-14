Save a reusable pattern/snippet in repo `docs/patterns/` + **ConPort** decision link (Memory Trinity).

1. Write `docs/patterns/<name>.md` with bullet list + code snippet.
2. Log decision: `mcp__conport__log_decision` with `workspace_id`, `topic`, `decision`, `tags: ["pattern"]`, and rationale linking the file path.

> Token thrift: prefer ConPort `search_content` and read only the top 3–5 results before full context.
