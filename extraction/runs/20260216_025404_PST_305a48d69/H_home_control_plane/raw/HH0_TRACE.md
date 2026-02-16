# SYSTEM PROMPT\n# Prompt H0: Inventory + partition plan (mandatory)

ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

TARGET PATHS (expand ~):
- ~/.dopemux
- ~/.config/dopemux
- ~/.config/taskx
- ~/.config/litellm
- ~/.config/mcp

OUTPUT 1: HOME_CONTROL_INVENTORY.json
For each file under these roots:
- path
- size_bytes
- last_modified
- file_kind: dir|text|json|yaml|toml|sqlite|binary|unknown
- sha256 if text and <= 1MB else null
- first_nonempty_line if text and <= 200KB else null
- contains_tokens[] from:
  ["mcp","litellm","router","provider","model","taskx","profile","session","hook","tmux","compose","dashboard","db","sqlite","postgres","token","key","secret"]

OUTPUT 2: HOME_CONTROL_PARTITION_PLAN.json
Create deterministic partitions with explicit file path lists:
H1_KEYS_AND_REFERENCES
H2_MCP
H3_ROUTER_AND_PROVIDER_LADDERS
H4_LITELLM
H5_PROFILES_AND_SESSIONS
H6_TMUX_AND_WORKFLOW
H7_SQLITE_AND_STATE_DB_META

RULES:
- Partitioning by path and filename heuristics only.
- JSON only.\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/.dopemux/mcp_config.json ---\n{
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