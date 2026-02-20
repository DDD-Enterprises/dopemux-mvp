# SYSTEM PROMPT\n# Prompt H9: Merge + QA

Outputs
normalized outputs under H_home_control_plane/norm/
H_COVERAGE_REPORT.json
ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS: all raw outputs H0-H7.

MERGE RULES:
- dedupe by (path, line_range, sha256(excerpt))
- stable sort by path then start line
- ensure each normalized output includes:
  - artifact_type
  - generated_at_local
  - inputs[] (file list)
  - items[]

QA OUTPUT: H_COVERAGE_REPORT.json
Include:
- expected_artifacts list
- present_artifacts list
- missing_artifacts list
- item_counts per artifact
- redaction_count
- db_count and table_count summary

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