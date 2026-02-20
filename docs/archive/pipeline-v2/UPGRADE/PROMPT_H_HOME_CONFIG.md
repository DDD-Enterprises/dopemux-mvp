---
id: PROMPT_H_HOME_CONFIG
title: Prompt H Home Config
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt H Home Config (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt H (v2): Home Config Pass

**Outputs:** `HOME_CONFIG_INVENTORY.json`, `HOME_CONFIG_KEYS.json`, `HOME_CONFIG_MCP_REFERENCES.json`, `HOME_CONFIG_DIFF_HINTS.json`

---

## TASK

Produce FOUR JSON files for home directory configuration analysis.

## TARGET PATHS (Allowlist Only)

Based on discovered paths:
- `~/.dopemux/**`
- `~/.config/dopemux/**`
- `~/.dopemux/litellm/**` (if exists)
- `~/.dopemux/mcp-tools/**` (if exists)

**Do NOT scan:**
- `~/.config/taskx` (not found)
- `~/.config/litellm` (not found)
- `~/.config/mcp` (not found)
- Any other `~/.config` subdirectories

## SAFETY & REDACTION RULES

**Never output raw secret values.**

### Redact Values Matching

Replace values of keys matching these patterns with `"REDACTED"`:
- `*key*`, `*token*`, `*secret*`, `*password*`, `*api*`, `*bearer*`, `*auth*`, `*cookie*`

### Redact Patterns Matching

Replace with `"REDACTED_PATTERN"`:
- Long base64 blobs (>32 characters)
- PEM blocks (`-----BEGIN`)
- JWT-ish patterns (`xxxxx.yyyyy.zzzzz`)
- 32+ character hex sequences
- API keys in comments

### Keep

- Filenames, server names, tool names
- Non-secret config keys
- Boolean flags
- Ports and localhost hostnames
- File paths (unless contain secrets)

## 1) HOME_CONFIG_INVENTORY.json

For each file:
- `path`: absolute path
- `size_bytes`: file size
- `sha256`: if available (optional)
- `last_modified`: if available
- `file_type`: extension or detected type

## 2) HOME_CONFIG_KEYS.json

### For JSON/YAML/TOML Files
Extract key paths only (not values unless safe):
- Key path: `"mcp.servers.local_files.command"`
- Include: `path`, `line_range` if possible
- Value: only if safe (boolean, number, non-secret string)

### For .env Style Files
Extract variable names only, **never values**:
- Variable name: `ANTHROPIC_API_KEY`
- Include: `path`, `line_range`
- Value: always `"REDACTED"`

## 3) HOME_CONFIG_MCP_REFERENCES.json

Extract literal references to:
- Server names (e.g., `dope_context`, `local_files`)
- Tool names
- `mcp_servers`, `tools`, `command`, `args` keys
- Endpoints/ports (keep unless credential-like)

Emit items:
- `ref_id`: `"home_ref:" + path + ":" + line_range[0] + ":" + ref_name`
- `path`, `line_range`
- `ref_type`: `mcp_server|mcp_tool|command|endpoint`
- `ref_name`: exact literal
- `excerpt`: <=4 lines (with secrets redacted)

## 4) HOME_CONFIG_DIFF_HINTS.json

Compare HOME_CONFIG_MCP_REFERENCES against repo files:
- `.claude.json`, `.claude/claude_config.json`
- `mcp-proxy-config*.yaml`, `mcp-proxy-config*.json`
- `.dopemux/mcp_config.json`
- `dopemux.toml`, `litellm.config*`

Output entries:
```json
{
  "item_name": "dope_context",
  "item_type": "mcp_server",
  "in_home": true,
  "in_repo": true,
  "home_paths": ["~/.dopemux/mcp-tools/config.json:12"],
  "repo_paths": [".claude/claude_config.json:45"],
  "drift_detected": false
}
```

If same server name appears in both but with different configs (different command, different args), set `drift_detected: true`.

## RULES

- **No interpretation, no "should"**
- **Never output secret values** - redact aggressively
- **JSON only**, ASCII only
- **Deterministic ordering** by path

## OUTPUT FORMAT

All four files follow this structure:
```json
{
  "artifact_type": "HOME_CONFIG_INVENTORY",
  "generated_at_utc": "2026-02-15T20:00:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "scanned_paths": [
    "~/.dopemux/**",
    "~/.config/dopemux/**"
  ],
  "items": [...]
}
```

## EXAMPLE (Redacted)

```json
{
  "path": "~/.dopemux/mcp_config.json",
  "line_range": [10, 15],
  "key_path": "servers.dope_context.env.ANTHROPIC_API_KEY",
  "value": "REDACTED"
}
```
