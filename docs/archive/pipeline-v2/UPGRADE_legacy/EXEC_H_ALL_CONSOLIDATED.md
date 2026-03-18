---
id: EXEC_H_ALL_CONSOLIDATED
title: Exec H All Consolidated
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Exec H All Consolidated (explanation) for dopemux documentation and developer
  workflows.
---
# EXECUTABLE PROMPT: H-ALL - Complete Home Config Extraction (Consolidated)

**Use this to run ALL home config phases (H1-H4) in a single API call.**

---

## YOUR ROLE

You are a **mechanical extractor with security awareness**. Extract home configuration structure, MCP/router/hooks/litellm surfaces, detect drift, and extract SQLite schemas. **NEVER output secret values.**

**CRITICAL: If you cannot comply with JSON-only output, output `{ "error": "NON_JSON_OUTPUT_REFUSED" }` and stop.**

---

## TASK

Run 4 subtasks and produce 8 JSON outputs in a single response.

Subtasks:
1. **H1: Inventory + Keys** → 2 files
2. **H2: MCP/Router/Hooks/LiteLLM Surfaces** → 4 files
3. **H3: Home vs Repo Diff Hints** → 1 file
4. **H4: SQLite Schemas** → 1 file

---

## SUBTASK H1: Inventory + Keys

### Allowlist
- `~/.dopemux/**`
- `~/.config/dopemux/**`

### Output 1: HOME_CONFIG_INVENTORY.json
List all files with: path, size_bytes, last_modified, extension, kind, is_sqlite

### Output 2: HOME_CONFIG_KEYS.json
Extract key paths (NO values) from JSON/YAML/TOML files.
Extract variable names (NO values) from .env files.

**Redaction:** Never output raw values. Use `"REDACTED"` for any sensitive keys.

---

## SUBTASK H2: MCP/Router/Hooks/LiteLLM Surfaces

### Scope (Include ONLY)
- `.dopemux/mcp_config.json`
- `.dopemux/mcp-tools/**`
- `.dopemux/claude-code-router/**`
- `.dopemux/dope-brainz-router/**`
- `.dopemux/litellm/**`
- `.dopemux/hook_status.json`
- `.config/dopemux/config.yaml`
- `.config/dopemux/dopemux.toml`
- `.dopemux/tmux-layout.sh`

### Output 3: HOME_MCP_SURFACE.json
Extract MCP server names, tool names, commands, endpoints (redact tokens).

### Output 4: HOME_ROUTER_SURFACE.json
Extract provider/model routing rules, fallback ladders, env var references.

### Output 5: HOME_HOOKS_SURFACE.json
Extract hook enablement flags, hook names, statuses from hook_status.json.

### Output 6: HOME_LITELLM_SURFACE.json
Extract proxy endpoints, database settings, spend tracking, model map keys (NO API keys).

**Redaction Rules:**
- Keys containing: `key`, `token`, `secret`, `password`, `api`, `auth` → `"REDACTED"`
- Long blobs, PEM, JWT patterns → `"REDACTED_PATTERN"`

---

## SUBTASK H3: Home vs Repo Diff Hints

### Inputs
Use outputs from H2 (MCP, router, litellm surfaces).

### Repo Files to Compare
Scan:
- `.claude/**`, `.claude.json*`
- `dopemux.toml`
- `mcp-proxy-config*.json/yaml`
- `compose.yml`, `docker-compose*.yml`
- `litellm.config*`

### Output 7: HOME_VS_REPO_DIFF_HINTS.json
For each item (server, tool, provider, endpoint):
- `item_name`, `item_type`, `in_home`, `in_repo`
- `home_paths[]`, `repo_paths[]`
- `drift_detected` (true if present in one but not other, or different config)
- `drift_reason` (string explanation or null)

**No arbitration** - just report differences.

---

## SUBTASK H4: SQLite Schemas

### Scope (Include ONLY)
- `~/.dopemux/context.db`
- `~/.dopemux/global_index.sqlite`

### Method
Extract schema ONLY (no table contents):
```sql
SELECT name, type, sql FROM sqlite_master 
WHERE type IN ('table', 'index', 'trigger', 'view');

PRAGMA user_version;
```

**DO NOT run:** `SELECT * FROM <table>`

### Output 8: HOME_SQLITE_SCHEMA.json
For each database:
- `db_path`, `db_size_bytes`, `user_version`
- `objects[]` with: `name`, `type`, `sql`

---

## OUTPUT FORMAT

Return a **single JSON object** containing all 8 outputs:

```json
{
  "h1_inventory": { /* HOME_CONFIG_INVENTORY.json content */ },
  "h1_keys": { /* HOME_CONFIG_KEYS.json content */ },
  "h2_mcp": { /* HOME_MCP_SURFACE.json content */ },
  "h2_router": { /* HOME_ROUTER_SURFACE.json content */ },
  "h2_hooks": { /* HOME_HOOKS_SURFACE.json content */ },
  "h2_litellm": { /* HOME_LITELLM_SURFACE.json content */ },
  "h3_diff": { /* HOME_VS_REPO_DIFF_HINTS.json content */ },
  "h4_sqlite": { /* HOME_SQLITE_SCHEMA.json content */ }
}
```

---

## HARD RULES

1. **JSON only** - No prose, no markdown, no explanations
2. **ASCII only** - No emoji, no special unicode
3. **Redact all secrets** - Never output API keys, tokens, passwords
4. **Schema only** for SQLite - No table contents
5. **No arbitration** for drift - Just report differences
6. **Deterministic sorting** - Sort by path alphabetically

---

## EXAMPLE STRUCTURE

```json
{
  "h1_inventory": {
    "artifact_type": "HOME_CONFIG_INVENTORY",
    "generated_at_utc": "2026-02-15T21:45:00Z",
    "files": [
      {
        "path": "~/.dopemux/mcp_config.json",
        "size_bytes": 1234,
        "kind": "json",
        "is_sqlite": false
      }
    ]
  },
  "h1_keys": {
    "artifact_type": "HOME_CONFIG_KEYS",
    "keys": [
      {
        "path": "~/.dopemux/mcp_config.json",
        "line_range": [5, 5],
        "key_path": "servers.dope_context.command",
        "value": "uv"
      }
    ]
  },
  "h2_mcp": {
    "artifact_type": "HOME_MCP_SURFACE",
    "refs": [ /* MCP server refs */ ]
  },
  "h2_router": {
    "artifact_type": "HOME_ROUTER_SURFACE",
    "routers": [ /* router configs */ ]
  },
  "h2_hooks": {
    "artifact_type": "HOME_HOOKS_SURFACE",
    "hooks": [ /* hook statuses */ ]
  },
  "h2_litellm": {
    "artifact_type": "HOME_LITELLM_SURFACE",
    "configs": [ /* litellm configs */ ]
  },
  "h3_diff": {
    "artifact_type": "HOME_VS_REPO_DIFF_HINTS",
    "comparisons": [
      {
        "item_name": "dope_context",
        "item_type": "mcp_server",
        "in_home": true,
        "in_repo": true,
        "drift_detected": false
      }
    ]
  },
  "h4_sqlite": {
    "artifact_type": "HOME_SQLITE_SCHEMA",
    "databases": [
      {
        "db_path": "~/.dopemux/context.db",
        "objects": [
          {
            "name": "events",
            "type": "table",
            "sql": "CREATE TABLE events (...)"
          }
        ]
      }
    ]
  }
}
```

---

## BEGIN EXTRACTION

Scan home configs and produce the consolidated JSON output now.

**Remember:**
- **REDACT ALL SECRETS**
- **SCHEMA ONLY for SQLite (no data)**
- **JSON ONLY output**
