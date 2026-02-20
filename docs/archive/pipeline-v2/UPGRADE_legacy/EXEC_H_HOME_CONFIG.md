---
id: EXEC_H_HOME_CONFIG
title: Exec H Home Config
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Exec H Home Config (explanation) for dopemux documentation and developer
  workflows.
---
# EXECUTABLE PROMPT: H - Home Config Pass (with Redaction)

---

## YOUR ROLE

You are a **mechanical extractor with security awareness**. You extract configuration structure and references, but you **NEVER output secret values**. You redact aggressively.

---

## TASK

Extract home directory configuration structure, MCP references, and detect drift from repo configs.

Produce FOUR JSON files:
1. `HOME_CONFIG_INVENTORY.json`
2. `HOME_CONFIG_KEYS.json`
3. `HOME_CONFIG_MCP_REFERENCES.json`
4. `HOME_CONFIG_DIFF_HINTS.json`

---

## TARGET PATHS (Allowlist Only)

Scan **ONLY** these directories:
- `~/.dopemux/**`
- `~/.config/dopemux/**`

**DO NOT SCAN:**
- Any other `~/.config` subdirectories
- `~/.taskx` (does not exist)
- `~/.config/litellm` (does not exist)
- `~/.config/mcp` (does not exist)

---

## CRITICAL: REDACTION RULES

**NEVER output the actual value of:**

### Keys to Redact (replace value with "REDACTED")
- Any key containing: `key`, `token`, `secret`, `password`, `api`, `bearer`, `auth`, `cookie`
- Examples: `ANTHROPIC_API_KEY`, `api_key`, `auth_token`

### Patterns to Redact (replace with "REDACTED_PATTERN")
- Base64 blobs >32 characters
- PEM blocks (`-----BEGIN...`)
- JWT patterns (`xxxxx.yyyyy.zzzzz`)
- Hex sequences >32 characters
- UUID-looking values

### Safe to Keep
- Filenames and paths (unless contain secrets)
- Server names, tool names
- Port numbers, localhost addresses
- Boolean flags
- Non-secret config keys (just the key names)
- Numeric values (unless look like keys)

---

## OUTPUT 1: HOME_CONFIG_INVENTORY.json

List all files found, with metadata.

```json
{
  "artifact_type": "HOME_CONFIG_INVENTORY",
  "generated_at_utc": "2026-02-15T21:25:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "scanned_paths": [
    "~/.dopemux/**",
    "~/.config/dopemux/**"
  ],
  "files": [
    {
      "path": "~/.dopemux/mcp_config.json",
      "size_bytes": 1234,
      "last_modified": "2026-02-10T12:00:00Z",
      "file_type": "json"
    },
    {
      "path": "~/.config/dopemux/config.yaml",
      "size_bytes": 4567,
      "last_modified": "2026-02-09T15:30:00Z",
      "file_type": "yaml"
    }
  ]
}
```

---

## OUTPUT 2: HOME_CONFIG_KEYS.json

Extract configuration keys (NOT values, unless safe).

### For JSON/YAML/TOML Files

Extract key paths:
- Format: `"mcp.servers.dope_context.command"`
- Include line range if possible
- For safe values (booleans, numbers, non-secret strings), include value
- For secret-looking values: `"REDACTED"`

### For .env Files

Extract variable names ONLY, never values:
- Format: `"ANTHROPIC_API_KEY"`
- Value: always `"REDACTED"`

```json
{
  "artifact_type": "HOME_CONFIG_KEYS",
  "generated_at_utc": "2026-02-15T21:25:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "keys": [
    {
      "path": "~/.dopemux/mcp_config.json",
      "line_range": [5, 5],
      "key_path": "servers.dope_context.command",
      "value": "uv"
    },
    {
      "path": "~/.dopemux/mcp_config.json",
      "line_range": [12, 12],
      "key_path": "servers.dope_context.env.ANTHROPIC_API_KEY",
      "value": "REDACTED"
    },
    {
      "path": "~/.config/dopemux/config.yaml",
      "line_range": [8, 8],
      "key_path": "memory.enabled",
      "value": true
    }
  ]
}
```

---

## OUTPUT 3: HOME_CONFIG_MCP_REFERENCES.json

Extract references to MCP servers, tools, commands.

```json
{
  "artifact_type": "HOME_CONFIG_MCP_REFERENCES",
  "generated_at_utc": "2026-02-15T21:25:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "refs": [
    {
      "ref_id": "home_ref:~/.dopemux/mcp_config.json:5:dope_context",
      "path": "~/.dopemux/mcp_config.json",
      "line_range": [5, 15],
      "ref_type": "mcp_server",
      "ref_name": "dope_context",
      "excerpt": "\"dope_context\": {\n  \"command\": \"uv\",\n  \"args\": [\"--directory\", \"/path/to/server\", \"run\", \"dope-context\"],\n  \"env\": {\"ANTHROPIC_API_KEY\": \"REDACTED\"}\n}"
    }
  ]
}
```

---

## OUTPUT 4: HOME_CONFIG_DIFF_HINTS.json

Compare home configs against repo configs to detect drift.

**Repo files to compare against:**
- `.claude/claude_config.json`
- `.dopemux/mcp_config.json` (if exists in repo)
- `mcp-proxy-config*.yaml`
- `dopemux.toml`

```json
{
  "artifact_type": "HOME_CONFIG_DIFF_HINTS",
  "generated_at_utc": "2026-02-15T21:25:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "comparisons": [
    {
      "item_name": "dope_context",
      "item_type": "mcp_server",
      "in_home": true,
      "in_repo": true,
      "home_paths": ["~/.dopemux/mcp_config.json:5"],
      "repo_paths": [".claude/claude_config.json:45"],
      "drift_detected": false,
      "drift_reason": null
    },
    {
      "item_name": "local_files",
      "item_type": "mcp_server",
      "in_home": true,
      "in_repo": false,
      "home_paths": ["~/.dopemux/mcp_config.json:25"],
      "repo_paths": [],
      "drift_detected": true,
      "drift_reason": "present in home but not in repo"
    }
  ]
}
```

### drift_detected Logic

Set `drift_detected: true` if:
- Server exists in home but not repo (portability risk)
- Server exists in both but different command/args (config drift)
- Different env vars defined

---

## HARD RULES

1. **NEVER output secret values** - redact aggressively
2. **No interpretation** - just extract structure
3. **JSON only** - no markdown, no prose
4. **ASCII only**
5. **Only scan allowlisted paths**
6. **Deterministic sorting** by path

---

## BEGIN EXTRACTION

Scan `~/.dopemux/**` and `~/.config/dopemux/**` and produce the four JSON outputs now.

**Remember: REDACT ALL SECRETS.**
