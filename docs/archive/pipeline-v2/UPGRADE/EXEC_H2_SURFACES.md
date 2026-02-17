---
id: EXEC_H2_SURFACES
title: Exec H2 Surfaces
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Exec H2 Surfaces (explanation) for dopemux documentation and developer workflows.
---
# EXECUTABLE PROMPT: H2 - Home MCP/Router/Hooks/LiteLLM Surface

---

## YOUR ROLE

You are a **mechanical extractor**. Extract MCP servers, router configs, hooks, and LiteLLM settings. Redact all secrets.

---

## TASK

Extract control plane surfaces from high-signal home config files.

Produce FOUR JSON files:
1. `HOME_MCP_SURFACE.json`
2. `HOME_ROUTER_SURFACE.json`
3. `HOME_HOOKS_SURFACE.json`
4. `HOME_LITELLM_SURFACE.json`

---

## SCOPE (Include ONLY These Files)

- `~/.dopemux/mcp_config.json`
- `~/.dopemux/mcp-tools/**`
- `~/.dopemux/claude-code-router/**`
- `~/.dopemux/dope-brainz-router/**`
- `~/.dopemux/litellm/**`
- `~/.dopemux/hook_status.json`
- `~/.config/dopemux/config.yaml`
- `~/.config/dopemux/dopemux.toml`
- `~/.dopemux/tmux-layout.sh`

**Do NOT scan:**
- sessions/, logs/, caches/, *.db files
- Any other directories

---

## OUTPUT 1: HOME_MCP_SURFACE.json

Extract MCP server and tool references:

```json
{
  "ref_id": "home_mcp:~/.dopemux/mcp_config.json:5:dope_context",
  "path": "~/.dopemux/mcp_config.json",
  "line_range": [5, 15],
  "ref_type": "mcp_server",
  "ref_name": "dope_context",
  "command": "uv",
  "args": ["--directory", "/path/to/server", "run", "dope-context"],
  "endpoint": null,
  "excerpt": "\"dope_context\": {\n  \"command\": \"uv\",\n  \"args\": [...],\n  \"env\": {\"ANTHROPIC_API_KEY\": \"REDACTED\"}\n}"
}
```

### Extract

- **Server names** (e.g., `dope_context`, `filesystem`)
- **Tool names** (if listed separately)
- **Command + args** (redact tokens in args)
- **Endpoints/ports** (keep unless credential-like)
- **Excerpt** (<=4 lines, with secrets redacted)

---

## OUTPUT 2: HOME_ROUTER_SURFACE.json

Extract routing and provider selection rules:

```json
{
  "router_id": "home_router:~/.dopemux/claude-code-router/config.yaml:12",
  "path": "~/.dopemux/claude-code-router/config.yaml",
  "line_range": [12, 20],
  "router_type": "provider_routing",
  "rule_name": "fallback_ladder",
  "content": "providers:\n  - anthropic\n  - openai\n  - xai\nfallback: true",
  "env_refs": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
}
```

### Extract

- **Provider/model routing rules**
- **Allow/deny lists**
- **Fallback ladders**
- **Environment variable references** (names only)
- **Excerpt** (<=4 lines)

---

## OUTPUT 3: HOME_HOOKS_SURFACE.json

Extract hook enablement and status:

```json
{
  "hook_id": "home_hook:~/.dopemux/hook_status.json:5:pre_commit",
  "path": "~/.dopemux/hook_status.json",
  "line_range": [5, 8],
  "hook_name": "pre-commit",
  "status": "enabled",
  "last_run": "2026-02-15T10:00:00Z"
}
```

### Extract

- **Hook names**
- **Enablement status** (enabled/disabled)
- **Last run timestamps** (if available)
- From `hook_status.json` and any hook config keys

---

## OUTPUT 4: HOME_LITELLM_SURFACE.json

Extract LiteLLM proxy and spend tracking config:

```json
{
  "litellm_id": "home_litellm:~/.dopemux/litellm/config.yaml:8",
  "path": "~/.dopemux/litellm/config.yaml",
  "line_range": [8, 15],
  "config_type": "proxy_endpoint",
  "content": "proxy:\n  endpoint: http://localhost:4000\n  database: REDACTED\n  spend_tracking: true",
  "model_map_keys": ["gpt-4", "claude-3"]
}
```

### Extract

- **Proxy endpoints**
- **Database settings** (redact connection strings)
- **Spend tracking toggles**
- **Model map keys** (model names, not API keys)

---

## REDACTION RULES

**Replace with "REDACTED":**
- Any value containing: `key`, `token`, `secret`, `password`, `api`, `auth`, `bearer`, `cookie`

**Replace with "REDACTED_PATTERN":**
- Long base64 blobs (>32 chars)
- PEM blocks (`-----BEGIN`)
- JWT patterns (`xxxxx.yyyyy.zzzzz`)
- 32+ character hex sequences

**Keep:**
- Server/tool names
- Endpoints (localhost, ports)
- Boolean flags
- Provider names (anthropic, openai, etc.)

---

## HARD RULES

1. **No inference** - extract literal text only
2. **JSON only** - no markdown, no prose
3. **ASCII only**
4. **Deterministic sorting** - by path, then line_range

---

## BEGIN EXTRACTION

Scan the specified files and produce the four JSON outputs now.

**Remember: REDACT ALL SECRETS.**
