# Git Worktree MCP Setup Guide

**Purpose**: Enable full MCP server functionality across all git worktrees with automatic workspace detection

## Overview

Git worktrees allow parallel development on different branches without context-switching overhead. This guide explains how MCP servers are configured to work seamlessly across all worktrees.

## Architecture

### Worktree Structure
```
Main Repo:    /Users/hue/code/dopemux-mvp (main branch)
  ├── .git/ (shared)
  ├── .claude/ (shared via git)
  └── .claude.json (per-worktree config)

Worktrees:
  ├── /Users/hue/code/ui-build (ui-build branch)
  │   └── .git → points to main repo
  └── /Users/hue/code/dopemux-worktree-test (test branch)
      └── .git → points to main repo
```

### What's Shared vs. Per-Worktree

**✅ Shared Across All Worktrees:**
- Git history (`.git/`)
- Project instructions (`.claude/`)
- ConPort decisions/progress (PostgreSQL database)
- Docker MCP containers (all worktrees use same containers)
- Global Claude config (`~/.claude.json`)

**🔀 Per-Worktree (Independent):**
- Working directory files
- Local `.claude.json` (optional - can override global)
- Branch-specific code changes

## MCP Server Configuration

### Workspace-Aware Servers

Some MCP servers need to know which worktree you're currently in:

**ConPort** - Decision logging, knowledge graph
- **Why**: Needs to tag decisions/progress with correct worktree context
- **Solution**: Wrapper script that auto-detects current worktree

**Serena** - LSP, code navigation
- **Why**: Needs to analyze code in the current worktree directory
- **Solution**: Wrapper script that passes current worktree path

### Workspace-Independent Servers

These servers provide global services and don't need worktree awareness:

- **Zen** - Multi-model reasoning (no workspace needed)
- **Context7** - Framework documentation (global reference)
- **GPT-Researcher** - Web research (no local files)
- **Exa** - Neural search (web-based)
- **Dope-Context** - Semantic code search (may be workspace-aware in future)

## Wrapper Scripts

Located in: `/Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/`

### ConPort Wrapper (`conport-wrapper.sh`)
```bash
#!/bin/bash
# Auto-detects workspace from:
# 1. CLAUDE_WORKSPACE env var (if set)
# 2. git rev-parse --show-toplevel (current git root)
# 3. Fallback to /Users/hue/code/dopemux-mvp

detect_workspace() {
    if [ -n "$CLAUDE_WORKSPACE" ]; then
        echo "$CLAUDE_WORKSPACE"
        return
    fi

    if command -v git &> /dev/null; then
        local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
        if [ -n "$git_root" ]; then
            echo "$git_root"
            return
        fi
    fi

    echo "/Users/hue/code/dopemux-mvp"
}

WORKSPACE_PATH=$(detect_workspace)
exec /Users/hue/code/dopemux-mvp/services/conport/venv/bin/conport-mcp \
    --workspace_id "$WORKSPACE_PATH" \
    "$@"
```

### Serena Wrapper (`serena-wrapper.sh`)
```bash
#!/bin/bash
# Same detection logic, passes WORKSPACE_PATH to docker container

detect_workspace() {
    # ... same as ConPort ...
}

WORKSPACE_PATH=$(detect_workspace)
exec docker exec \
    -e WORKSPACE_PATH="$WORKSPACE_PATH" \
    -i mcp-serena \
    python /app/wrapper.py \
    "$@"
```

## Setting Up MCP Servers in a New Worktree

### Quick Setup (Recommended)
```bash
# Navigate to your worktree
cd /Users/hue/code/your-worktree

# Add all Dopemux MCP servers
claude mcp add conport /Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/conport-wrapper.sh
claude mcp add serena /Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/serena-wrapper.sh
claude mcp add zen -- docker exec -i mcp-zen bash -c "source .venv/bin/activate && python server.py"
claude mcp add context7 -- npx -y @context7/mcp-server
claude mcp add gpt-researcher -- docker exec -e MCP_TRANSPORT=stdio -i dopemux-mcp-gptr-mcp python /app/server.py
claude mcp add exa -- uvx exa-mcp
claude mcp add dope-context /Users/hue/code/dopemux-mvp/services/dope-context/run_mcp.sh
claude mcp add serena-v2 -- python3 /Users/hue/code/dopemux-mvp/services/serena/v2/mcp_server.py
```

### Verification
```bash
# Check MCP servers are configured
claude mcp list

# Start a new Claude Code session to activate servers
# In the new session, test with:
# /mcp
```

## Claude Desktop vs Claude Code

**Important**: Claude Desktop (GUI) and Claude Code (CLI) have SEPARATE MCP configurations!

**Claude Desktop (GUI):**
- Config: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Updated with workspace-aware wrappers for ConPort and Serena
- Used when running Claude Desktop app

**Claude Code (CLI):**
- Config: `~/.claude.json` (global, per-project sections)
- Updated with `claude mcp add` commands
- Used when running `claude` command in terminal

## Troubleshooting

### MCP Servers Not Appearing
1. **Check if configured**: `claude mcp list`
2. **Verify wrappers are executable**: `ls -la /Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/`
3. **Restart Claude Code session**: Exit conversation and start new one
4. **Check docker containers**: `docker ps | grep mcp`

### Wrong Workspace Detected
1. **Check git root**: `git rev-parse --show-toplevel`
2. **Manually set**: `export CLAUDE_WORKSPACE=/path/to/worktree`
3. **Check wrapper logs**: Wrappers log detected workspace to stderr

### ConPort Can't Find Decisions
- ConPort stores data in PostgreSQL (shared across worktrees)
- Check container: `docker ps | grep conport`
- Check connection: `curl http://localhost:3004/health`

### Serena Can't Find Code
- Serena needs correct WORKSPACE_PATH
- Check wrapper detected correct path
- Verify files exist in worktree: `ls -la /path/to/worktree`

## Best Practices

### 1. Use Main Repo for Infrastructure
- Keep docker containers running from main repo
- Store wrapper scripts in main repo
- Use main repo for database migrations

### 2. Use Worktrees for Feature Development
- Create worktree per feature/branch
- Configure MCP servers once per worktree
- Delete worktree when branch is merged

### 3. ConPort Tagging Strategy
- Tag decisions with worktree name in metadata
- Use `custom_data` to store worktree context
- Link progress entries to worktree-specific tasks

### 4. Memory Management
```bash
# Log decision with worktree context
mcp__conport__log_decision \
  --workspace_id "$(git rev-parse --show-toplevel)" \
  --summary "Feature X implementation decision" \
  --tags "worktree:ui-build"

# Query decisions for current worktree
mcp__conport__get_decisions \
  --workspace_id "$(git rev-parse --show-toplevel)" \
  --tags "worktree:$(basename $(git rev-parse --show-toplevel))"
```

## Advanced: Multiple Worktree Workflows

### Parallel Feature Development
```bash
# Worktree 1: UI work
cd /Users/hue/code/ui-build
claude  # Works on UI with full MCP access

# Worktree 2: Backend work
cd /Users/hue/code/backend-work
claude  # Works on backend with full MCP access

# Both can run simultaneously with isolated contexts!
```

### Context Switching
```bash
# Save context in current worktree
mcp__conport__update_active_context \
  --workspace_id "$(git rev-parse --show-toplevel)" \
  --patch_content '{"paused": true, "paused_at": "2025-10-16T02:30:00Z"}'

# Switch to different worktree
cd /Users/hue/code/other-worktree

# Resume context
mcp__conport__get_active_context \
  --workspace_id "$(git rev-parse --show-toplevel)"
```

## ADHD Benefits of Worktrees

### Context Preservation
- Each worktree maintains independent state
- No mental switching cost when changing tasks
- Physical directory separation = clear mental boundaries

### Interrupt-Safe
- Pause one worktree, switch to another without losing progress
- All MCP servers work correctly in each worktree
- ConPort preserves decisions/progress per worktree

### Main Branch Protection
- Never work directly on main (worktrees enforce this)
- Clean separation of stable code vs. in-progress work
- Easy rollback (just delete worktree)

## Files Modified

This setup required changes to:

1. **Created**:
   - `/Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/conport-wrapper.sh`
   - `/Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/serena-wrapper.sh`

2. **Modified**:
   - `~/Library/Application Support/Claude/claude_desktop_config.json` (Claude Desktop)
   - `~/.claude.json` (Claude Code global config, per-project sections)

3. **Documented**:
   - This file: `.claude/WORKTREE_MCP_SETUP.md`
   - Global: `~/.claude/CLAUDE.md` (worktree section added)

## Future Enhancements

- [ ] Auto-setup script for new worktrees
- [ ] Worktree-specific ConPort tagging (automatic)
- [ ] Dope-Context workspace awareness
- [ ] Multi-worktree status dashboard
- [ ] Worktree session recovery automation

---

**Status**: ✅ Fully operational across all worktrees
**Last Updated**: 2025-10-16
**Tested**: ui-build, dopemux-worktree-test worktrees
