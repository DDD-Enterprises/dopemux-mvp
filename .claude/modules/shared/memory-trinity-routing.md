# Memory Trinity Routing Card

**Module Version**: 1.0.0
**Authority**: Accepted ADR law (2026-06-19)
**ADR**: `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md`

## The Three Planes (never interchangeable)

| Plane | Canonical for | MCP | Write? |
|-------|---------------|-----|--------|
| **ConPort** | Decisions, progress, durable structured context, knowledge graph | `mcp__conport__*` (singleton in `~/.claude.json` + per-worktree ports) | Yes — canonical writer |
| **dope-memory** | Chronicle, replay, recap, reflection, trajectory | `mcp__dope-memory__*` (per-worktree `.mcp.json`) | Yes — chronicle only; mirrors ConPort writes |
| **dope-context** | Semantic retrieval over indexed code/docs | `mcp__dope-context__*` (singleton `http://localhost:3010/mcp`) | **No** — retrieval/index only |

**Forbidden backends (removed from operator surface):** OpenMemory, Mem0, `memory_bank`, generic `/mcp memory`.

## Operator routing (which tool for which intent)

| Intent | Route to | Example |
|--------|----------|---------|
| Log architectural decision | ConPort | `mcp__conport__log_decision` |
| Log task progress | ConPort | `mcp__conport__log_progress` |
| Scratch / ephemeral notes | ConPort | `mcp__conport__log_custom_data` category `scratch` |
| Search past decisions | ConPort | `mcp__conport__search_decisions_fts` |
| Session context checkpoint | Dopemux CLI | `dopemux save` / `/save` → `.dopemux/context.db` |
| Work chronicle / recap | dope-memory | Mirror receipt after ConPort write; direct chronicle tools when exposed |
| Find code by meaning | dope-context | `mcp__dope-context__search_code` |
| Find docs by meaning | dope-context | `mcp__dope-context__docs_search` |
| Unified code+docs search | dope-context | `mcp__dope-context__search_all` (decisions are DERIVED projection, limit ≤10) |
| Navigate symbols / LSP | Serena | `mcp__serena__*` — technical context plane, not Memory Trinity |

## Cross-plane rules

1. **ConPort writes first** for decisions/progress; dope-memory mirrors (see `memory_writers.py`).
2. **dope-context may project** ConPort decisions into search results but must not become the decision store.
3. **Retrieval ≠ truth** — ranked snippets are evidence, not canonical objects.
4. **Fail closed** when the target MCP is unreachable; do not fall back to a different plane silently.

## MCP wiring checklist

**Per-worktree** (`.mcp.json` via `dopemux mcp init`):
- `conport`, `dope-memory`, `task-orchestrator`

**Singletons** (`~/.claude.json` via `dopemux mcp sync-globals --apply`):
- `dope-context` → `http://localhost:3010/mcp`
- `serena`, `pal`, etc.

**Verify:**
```bash
docker ps --filter name=dope-context --format '{{.Status}}'
dopemux mcp doctor
curl -s http://127.0.0.1:3010/mcp -X POST \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}'
```

## Slash command map (post-remediation)

| Command | Plane |
|---------|-------|
| `/decision`, `/caveat`, `/followup`, `/scratch` | ConPort |
| `/get-decisions`, `/search-decisions` | ConPort |
| `/ctx:search-here`, `/ctx:index-search` | dope-context |
| `/save` | Dopemux local checkpoint (not Trinity) |
| `/mem:recap` (planned) | dope-memory |