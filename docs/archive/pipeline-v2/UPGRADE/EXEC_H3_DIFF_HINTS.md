---
id: EXEC_H3_DIFF_HINTS
title: Exec H3 Diff Hints
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Exec H3 Diff Hints (explanation) for dopemux documentation and developer
  workflows.
---
# EXECUTABLE PROMPT: H3 - Home vs Repo Diff Hints

---

## YOUR ROLE

You are a **mechanical differ**. Compare home configs against repo configs. Do NOT arbitrate which is correct.

---

## TASK

Detect configuration drift between home directory and repository.

Produce ONE JSON file: `HOME_VS_REPO_DIFF_HINTS.json`

---

## INPUTS

### Home Config Artifacts (from H2)
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_LITELLM_SURFACE.json`

### Repo Files to Compare Against

Scan these repo files:
- `.claude/**`
- `.claude.json*`
- `.dopemux/**` (if exists in repo)
- `dopemux.toml`
- `mcp-proxy-config*.json`
- `mcp-proxy-config*.yaml`
- `compose.yml`
- `docker-compose*.yml`
- `litellm.config*`

---

## OUTPUT: HOME_VS_REPO_DIFF_HINTS.json

For each item (server, tool, provider, model, endpoint, env var):

```json
{
  "item_name": "dope_context",
  "item_type": "mcp_server",
  "in_home": true,
  "in_repo": true,
  "home_paths": ["~/.dopemux/mcp_config.json:5"],
  "repo_paths": [".claude/claude_config.json:45"],
  "drift_detected": false,
  "drift_reason": null,
  "excerpt_refs": [
    {
      "source": "home",
      "path": "~/.dopemux/mcp_config.json",
      "line_range": [5, 15],
      "excerpt": "\"dope_context\": {\"command\": \"uv\", ...}"
    },
    {
      "source": "repo",
      "path": ".claude/claude_config.json",
      "line_range": [45, 55],
      "excerpt": "\"dope_context\": {\"command\": \"uv\", ...}"
    }
  ]
}
```

### item_type Values

- `mcp_server`
- `mcp_tool`
- `provider`
- `model`
- `endpoint`
- `env_var`
- `router_rule`
- `hook`

### drift_detected Logic

Set `drift_detected: true` if:
- Item exists in home but NOT in repo (portability risk)
- Item exists in both but different configuration:
  - Different command/args for MCP servers
  - Different endpoints
  - Different env vars required
  - Different provider ordering
- Item exists in repo but NOT in home (unused/dead code)

### drift_reason Examples

- `"present in home but not in repo"`
- `"different command: home uses 'uv', repo uses 'npx'"`
- `"different endpoint: home localhost:4000, repo localhost:8080"`
- `"present in repo but not in home (possibly unused)"`
- `null` (if no drift)

---

## EXTRACTION RULES

1. **Extract item names** from home artifacts
2. **Scan repo files** for same item names (literal string match)
3. **Compare presence and configuration**
4. **Do NOT decide which side is correct**
5. **Just report differences**

---

## HARD RULES

1. **No arbitration** - don't say "repo should..." or "home is wrong"
2. **JSON only** - no markdown, no prose
3. **ASCII only**
4. **Deterministic sorting** - by item_name

---

## EXAMPLE OUTPUT

```json
{
  "artifact_type": "HOME_VS_REPO_DIFF_HINTS",
  "generated_at_utc": "2026-02-15T21:40:00Z",
  "source_artifact": "HOME_DIRECTORY + WORKING_TREE",
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
    },
    {
      "item_name": "litellm_proxy",
      "item_type": "endpoint",
      "in_home": true,
      "in_repo": true,
      "home_paths": ["~/.dopemux/litellm/config.yaml:8"],
      "repo_paths": ["compose.yml:67"],
      "drift_detected": true,
      "drift_reason": "different endpoint: home localhost:4000, repo localhost:8080"
    }
  ]
}
```

---

## BEGIN EXTRACTION

Read the home artifacts and scan repo files. Produce the diff hints JSON now.
