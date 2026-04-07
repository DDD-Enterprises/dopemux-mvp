---
id: serena-v2-mcp-tools
title: Serena V2 MCP Tools
type: reference
owner: '@hu3mann'
last_review: '2026-03-31'
next_review: '2026-06-29'
author: '@hu3mann'
date: '2026-03-31'
prelude: Current local Serena MCP tool reference for the repo-hosted implementation candidate.
---
# Serena v2 MCP Tool Reference

## Status

- Current file authority: `services/serena/mcp_server.py`
- Local tool count: `33`
- Local runtime status: `implementation_candidate`
- Deployed runtime status: the repo-proven deployed Serena path is still the dockerized wrapper, not this local MCP server

Current deployment/runtime authority:

- [capability-manifest.md](/Users/hue/code/dopemux-mvp/docs/systems/serena/capability-manifest.md)
- [deployment-alignment-and-sanctioned-contract.md](/Users/hue/code/dopemux-mvp/docs/systems/serena/deployment-alignment-and-sanctioned-contract.md)
- [runtime-candidate-inventory.md](/Users/hue/code/dopemux-mvp/docs/systems/serena/runtime-candidate-inventory.md)

## Local MCP tool groups

### Files

- `read_file`
- `list_dir`

### Health

- `get_workspace_status`

### Tier 1 navigation

- `find_symbol`
- `goto_definition`
- `get_context`
- `find_references`

### Tier 2 ADHD intelligence

- `analyze_complexity`
- `filter_by_focus`
- `suggest_next_step`
- `get_reading_order`

### Enhanced navigation

- `find_similar_code`
- `predict_navigation_from_git`
- `find_test_file`
- `get_unified_complexity`

### Tier 3 advanced intelligence

- `find_relationships`
- `get_navigation_patterns`
- `update_focus_mode`

### Feature 1 detection, actions, config, and metrics

- `detect_untracked_work`
- `track_untracked_work`
- `snooze_untracked_work`
- `ignore_untracked_work`
- `suggest_branch_organization`
- `get_pattern_stats`
- `get_top_patterns`
- `get_abandoned_work`
- `mark_abandoned`
- `get_abandonment_stats`
- `get_metrics_dashboard`
- `get_metric_history`
- `save_metrics_snapshot`
- `get_untracked_work_config`
- `update_untracked_work_config`

## Current behavior notes

- Local LSP-backed navigation uses `EnhancedLSPWrapper`, not `SimpleLSPClient`.
- Tier 3 tools are no longer documented here as placeholders:
  - `find_relationships` prefers PostgreSQL graph data and falls back explicitly.
  - `get_navigation_patterns` prefers persisted `navigation_patterns` data and reports explicit degraded status when unavailable.
  - `update_focus_mode` persists mapped preferences into `learning_profiles` when the intelligence database is available.
- Multi-workspace behavior is implemented by `services/serena/multi_workspace_wrapper.py` using pinned per-workspace Serena instances.

## Validation

Validated locally on `2026-03-31`:

- `pytest services/serena --collect-only -q` succeeds from repo root
- `pytest services/serena -q` exits `0` with database-gated skips when local Postgres test initialization is unavailable
