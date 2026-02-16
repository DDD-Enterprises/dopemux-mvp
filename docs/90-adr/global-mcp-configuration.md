---
id: global-mcp-configuration
title: Global Mcp Configuration
type: adr
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Global Mcp Configuration (adr) for dopemux documentation and developer workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# Decision: Global MCP Configuration for Dopemux Platform-Wide Availability

**Date**: 2025-10-16
**Status**: Implemented
**Decision ID**: TBD (to be logged to ConPort)

## Problem

When working in the `code-cleanup` worktree, `/mcp` command showed "No MCP servers configured", even though MCP servers were running and should be available. This revealed a fundamental architectural mismatch:

- **Per-Project Config**: Each project/worktree in `~/.claude.json` had its own `mcpServers` configuration
- **Duplication**: 11 projects × 8 MCP servers = 88 duplicate config entries
- **Broken Inheritance**: New worktrees started with empty MCP config
- **Violated DRY**: Updating MCP servers required changes in 11+ places
- **Wrong Mental Model**: Treated Dopemux as "a project" not "a platform"

## Root Cause

Claude Code treats each git worktree as a separate project in `~/.claude.json`. Without explicit configuration inheritance, each worktree starts with empty `mcpServers`, even though they're part of the same repository.

## Solution: Global MCP Configuration

**Architectural Decision**: Dopemux is a development PLATFORM, not just a project.

MCP servers and ADHD-optimized workflows should work **identically everywhere**:
- Main repository
- All worktrees (code-cleanup, ui-build, etc.)
- Even unrelated projects (if desired)

**Implementation**: Migrated all 8 Dopemux MCP servers from per-project config to global config:

**Before** (Per-Project):
```json
{
  "projects": {
    "/Users/hue/code/dopemux-mvp": {
      "mcpServers": { /* 8 servers */ }
    },
    "/Users/hue/code/code-cleanup": {
      "mcpServers": {} // Empty!
    }
    // ... 9 more projects
  }
}
```

**After** (Global):
```json
{
  "mcpServers": {
    "pal": {...},
    "conport": {...},
    "exa": {...},
    "mas-sequential-thinking": {...},
    "dope-context": {...},
    "serena-v2": {...},
    "zen": {...},
    "gpt-researcher": {...}
  },
  "projects": {
    // Projects can override but inherit global by default
  }
}
```

## Benefits

1. ✅ **DRY Principle**: Configure once, works everywhere
1. ✅ **Worktree-Friendly**: All worktrees automatically get full Dopemux stack
1. ✅ **New Projects**: Any new project gets Dopemux superpowers immediately
1. ✅ **Consistent Experience**: `~/.claude/CLAUDE.md` + global MCPs = Consistent everywhere
1. ✅ **Maintainable**: Update one place, not 11+ projects
1. ✅ **Platform Thinking**: Aligns with "Dopemux is a platform" philosophy

## Architecture Pattern

**Dopemux Platform Stack = Global Config + Global Tools**

```
~/.claude/CLAUDE.md          (Global behavioral rules)
    ↓
~/.claude.json mcpServers    (Global tool availability)
    ↓
Consistent Dopemux Experience Everywhere
```

## MCP Servers in Global Config

All 8 servers now available globally:

1. **pal**: Official framework documentation (React, Next.js, etc.)
1. **conport**: Decision logging, knowledge graph, ADHD task management
1. **exa**: Fast neural web search
1. **mas-sequential-thinking**: Multi-step reasoning (may be replaced by Zen)
1. **dope-context**: AST-aware code search, semantic doc search
1. **serena-v2**: LSP code navigation with ADHD optimizations
1. **zen**: Multi-model reasoning (thinkdeep, planner, consensus, debug, codereview)
1. **gpt-researcher**: Deep multi-source research with synthesis

## Impact

- **Immediate**: All worktrees now have full MCP access
- **Development**: No more "MCP not configured" errors
- **Maintenance**: Single source of truth for MCP config
- **Scalability**: New worktrees/projects work out of the box

## Tags

`#mcp-configuration` `#architecture-decision` `#worktree-support` `#adhd-optimization` `#platform-design` `#dry-principle`

## Next Steps

1. ✅ Global config implemented and verified
1. ⏳ Log this decision to ConPort (on next session with MCP reload)
1. ⏳ Document in project architecture docs
1. ⏳ Update WORKTREE_MCP_SETUP.md with new approach

ion to ConPort (on next session with MCP reload)
1. ⏳ Document in project architecture docs
1. ⏳ Update WORKTREE_MCP_SETUP.md with new approach
