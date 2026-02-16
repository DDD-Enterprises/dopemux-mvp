# SYSTEM PROMPT\n# Prompt H1: Keys + references (where home config points into repo/world)

Outputs
HOME_KEYS_SURFACE.json
HOME_REFERENCES.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- any text/json/yaml/toml file in partitions H1/H3/H4

TASK 1: HOME_KEYS_SURFACE.json
Extract key structure only:
- For YAML/TOML/JSON:
  - top-level keys
  - nested key paths up to depth=6
  - do not include values unless value is boolean/number or a safe enum word
- For non-structured text:
  - extract lines that look like KEY=VALUE but output only KEY and redacted indicator

Each item:
- path, line_range
- key_paths[] (e.g., "mcp.servers.local_files.command")
- value_kind for each path: string|number|bool|list|object|unknown
- safe_value if bool/number else null

TASK 2: HOME_REFERENCES.json
Extract literal references to:
- file paths
- URLs
- command invocations
- environment variable names
- sockets/ports (e.g., :4000)
For each reference:
- ref_kind: path|url|command|env|port
- value (literal, but redact secrets)
- path, line_range, excerpt <= 6 lines

REDACTION:
- If value contains "token", "key", "secret", "pass", or looks like a long random string, output "***REDACTED***"
- Never output private keys or credential blobs.

JSON only.\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/.dopemux/mcp_config.json ---\n{
  "mcpServers": {
    "claude-context": {
      "command": "npx",
      "args": ["-y", "@zilliz/claude-context-mcp@latest"],
      "capabilities": {
        "description": "Semantic code search using embeddings",
        "features": {
          "semantic_search": "Search code by meaning",
          "embedding_index": "Chroma-backed index",
          "codebase_navigation": "Find implementations and usages"
        }
      }
    }
  }
}
\n\n--- FILE: /Users/hue/.dopemux/instances_cache.json ---\n{
  "timestamp": 1770630779.4899998,
  "instances": []
}\n\n--- FILE: /Users/hue/.dopemux/tmux-layout.sh ---\n#!/usr/bin/env bash
session="dopemux"
tmux has-session -t "$session" 2>/dev/null && { echo "Session exists."; exit 0; }
tmux new-session -d -s "$session" -n orchestration
tmux split-window -v
tmux send-keys -t "${session}:0.0" 'claude-flow start --master --memory ~/.dopemux/memory/claude-flow.db' C-m
tmux send-keys -t "${session}:0.1" 'claude-flow monitor' C-m
tmux new-window -t "$session" -n execution
tmux split-window -v
tmux new-window -t "$session" -n memory
tmux split-window -v
tmux new-window -t "$session" -n project
tmux split-window -v
echo "Dopemux tmux session created. Attach with: tmux attach -t ${session}"
\n\n--- FILE: /Users/hue/.dopemux/hook_status.json ---\n{"monitoring_active": true, "watched_paths": ["/Users/hue/code/dopemux-mvp", "/Users/hue/.claude", "/Users/hue/code"], "pid": 36331}\n\n--- FILE: /Users/hue/.dopemux/claude-code-router/A/.claude.json ---\n{
  "numStartups": 184,
  "autoUpdaterStatus": "enabled",
  "userID": "39f8666492961dd3a7cb3bf553eb750310164e32935f828b8758ebec7766f118",
  "hasCompletedOnboarding": true,
  "lastOnboardingVersion": "1.0.17",
  "projects": {}
}\n\n--- FILE: /Users/hue/.dopemux/claude-code-router/A/.claude-code-router/config.json ---\n{
  "PORT": 3456,
  "HOST": "127.0.0.1",
  "LOG": true,
  "LOG_LEVEL": "info",
  "NON_INTERACTIVE_MODE": true,
  "API_TIMEOUT_MS":... [truncated for trace]