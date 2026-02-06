# Global MCP Configuration for Dopemux Platform

**Date**: 2025-10-16
**Decision ID**: Global MCP Migration
**Status**: Implemented ✅

## Problem

Claude Code treats each git worktree as a separate project with independent MCP configuration. This creates several issues for Dopemux as a development platform:

1. **DRY Violation**: Same 8 MCP servers configured in 11+ different project paths
2. **Worktree Friction**: Every new worktree requires manual MCP setup
3. **Inconsistency**: Different projects might have different MCP configurations
4. **Maintenance Burden**: Updating one MCP server requires 11+ edits
5. **Platform Philosophy**: Dopemux is a platform, not just a project

## Solution

**Migrate all Dopemux MCP servers to global configuration** in `~/.claude.json`:

```json
{
  "mcpServers": {
    // GLOBAL: All 8 Dopemux MCPs available everywhere
    "PAL apilookup": {...},
    "conport": {...},
    "serena-v2": {...},
    "zen": {...},
    "dope-context": {...},
    "gpt-researcher": {...},
    "exa": {...},
    "mas-sequential-thinking": {...}
  },
  "projects": {
    // Projects can OVERRIDE but inherit global by default
    "/Users/hue/code/dopemux-mvp": {
      "mcpServers": {}  // Empty = uses global
    },
    "/Users/hue/code/code-cleanup": {
      "mcpServers": {}  // Empty = uses global
    }
  }
}
```

## Benefits

### ✅ DRY (Don't Repeat Yourself)
- Configure once in global `mcpServers`
- All projects automatically inherit
- Single source of truth

### ✅ Worktree-Friendly
- New worktrees automatically get full Dopemux stack
- Zero configuration needed
- Consistent experience across all worktrees

### ✅ Platform-Level Operation
- Dopemux MCPs work everywhere, not just in Dopemux projects
- ADHD-optimized workflows available in ANY project
- `~/.claude/CLAUDE.md` + global MCPs = universal Dopemux experience

### ✅ Easy Maintenance
- Update MCP server: Edit one place in `~/.claude.json`
- All projects immediately get the update
- No need to track down duplicate configs

### ✅ Project Overrides Still Possible
- Projects can override specific MCPs if needed
- Empty `mcpServers: {}` = use global (recommended)
- Non-empty = override global for this project only

## Migration Process

**Backup First** (CRITICAL):
```bash
cp ~/.claude.json ~/.claude.json.backup-pre-global-mcp-$(date +%Y%m%d-%H%M%S)
```

**Migration Script**:
```python
import json

with open('/Users/hue/.claude.json', 'r') as f:
    data = json.load(f)

# Get dopemux-mvp MCP config (source of truth)
dopemux_mcps = data['projects']['/Users/hue/code/dopemux-mvp']['mcpServers']

# Move to global
data['mcpServers'] = dopemux_mcps

# Clear all project-specific configs
for project_config in data['projects'].values():
    project_config['mcpServers'] = {}

# Save
with open('/Users/hue/.claude.json', 'w') as f:
    json.dump(data, f, indent=2)
```

**Verification**:
```bash
claude mcp list  # Should show all 8 servers from any directory
```

## Results

**Before Migration**:
- 4 projects with duplicate MCP configs (dopemux-mvp, code-cleanup, ui-build, zen-mcp-server)
- 7 projects with zero MCP configs
- Total: 21 duplicated server definitions

**After Migration**:
- 8 global MCP servers
- 11 projects all using global (empty `mcpServers: {}`)
- Zero duplication

**Server List** (Global):
1. `PAL apilookup` - Official framework documentation
2. `conport` - Knowledge graph and decision logging
3. `serena-v2` - LSP-based code navigation
4. `zen` - Multi-model reasoning suite
5. `dope-context` - Semantic code & docs search
6. `gpt-researcher` - Deep multi-source research
7. `exa` - Fast neural search
8. `mas-sequential-thinking` - Legacy sequential reasoning

## Claude Code Architecture

Claude Code supports **three levels** of MCP configuration:

1. **Global** (`mcpServers` at root level): Available everywhere
2. **Project-Specific** (`projects[path].mcpServers`): Override global for specific paths
3. **Local** (`.mcp.json` in project): Committed to git, team-level config

**Dopemux Uses**: Global (level 1) for platform stack

## Future Considerations

### When to Use Project-Specific Overrides
- Project has conflicting MCP server (rare)
- Project needs different version of an MCP
- Project-specific tools that shouldn't be global

### When to Use Local `.mcp.json`
- Team collaboration (committed to git)
- Project-specific tools for all team members
- Different from Dopemux platform stack

### Potential Enhancements
- Auto-detect new worktrees and verify global MCP availability
- Script to sync MCP configs across multiple machines
- Health check to ensure all 8 servers are running

## Testing

**Verify Global MCPs Work Everywhere**:
```bash
# Test in main repo
cd /Users/hue/code/dopemux-mvp
claude mcp list  # Should show 8 servers

# Test in worktree
cd /Users/hue/code/code-cleanup
claude mcp list  # Should show same 8 servers

# Test in random project
cd ~/code/some-other-project
claude mcp list  # Should show same 8 servers
```

**Expected Output**:
```
✓ Connected: PAL apilookup, conport, dope-context, serena-v2, zen, gpt-researcher
✗ Failed: exa (known issue)
✓ Connected: mas-sequential-thinking
```

## Rollback

If global MCPs cause issues:

```bash
# Restore from backup
cp ~/.claude.json.backup-pre-global-mcp-TIMESTAMP ~/.claude.json

# Restart Claude Code
```

## Documentation Updates Needed

- [ ] Update `~/.claude/MCP_*.md` docs to reflect global config
- [ ] Update `.claude/CLAUDE.md` to mention global MCP approach
- [ ] Document in Dopemux main README
- [ ] Add to worktree setup guide

---

**Architecture Decision**: Global MCP configuration aligns with Dopemux's platform philosophy - consistent ADHD-optimized development experience everywhere, not just in Dopemux projects.
