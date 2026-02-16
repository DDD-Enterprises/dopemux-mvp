# SYSTEM PROMPT\n# Prompt H5: Profiles + sessions (home)

Outputs
HOME_PROFILES_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- ~/.dopemux/profiles/**
- ~/.dopemux/sessions/**
- ~/.config/dopemux/profiles/**

Extract:
- profile file names and key paths (no sensitive values)
- session metadata (file names, timestamps)
- any references to workflows, servers, models, task packets

Each item:
- item_kind: profile|session|cache
- path
- size_bytes
- detected_tokens[] from ["workflow","task","packet","model","provider","server","mcp","litellm"]
- for text: key_paths[] up to depth=5
- for json: top-level keys

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