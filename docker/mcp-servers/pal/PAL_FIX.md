# Zen MCP Fix: Unsupported CLI Configurations

**Date**: 2025-10-16
**Issue**: Server crashes on startup with `RegistryLoadError: CLI 'claude-main' is not supported by clink`

## Root Cause

The clink registry (CLI bridge component) only supports specific CLI names defined in `INTERNAL_DEFAULTS`:
- claude
- codex  
- gemini

Custom configs like `claude-main`, `claude-test`, `claude-ui` cause crashes because they're not in the supported list.

## Fix Applied

Disabled unsupported CLI config files:
```bash
conf/cli_clients/claude-main.json → claude-main.json.disabled
conf/cli_clients/claude-test.json → claude-test.json.disabled
conf/cli_clients/claude-ui.json → claude-ui.json.disabled
```

## Verification

```bash
docker exec -i mcp-zen bash -c "source .venv/bin/activate && python server.py"
# Successfully initializes with 12 active tools
```

## Active Tools (12)
- thinkdeep, planner, consensus, debug, codereview
- chat, clink, precommit, challenge, apilookup, listmodels, version

## Impact

✅ Zen-MCP now connects properly to Claude Code
✅ All reasoning tools available (thinkdeep, planner, consensus, etc.)
✅ Worktree-independent (works from any directory)

## Worktree Support

Zen-MCP is **workspace-independent**:
- Provides reasoning tools via Docker container
- No persistent state tied to specific workspaces
- Works identically from main repo or any worktree
- No worktree-specific configuration needed

