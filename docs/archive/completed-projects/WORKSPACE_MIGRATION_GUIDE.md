---
id: WORKSPACE_MIGRATION_GUIDE
title: Workspace_Migration_Guide
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Workspace_Migration_Guide (explanation) for dopemux documentation and developer
  workflows.
---
# Multi-Workspace Migration Guide

**Upgrading existing Dopemux installations to support multi-workspace**

## Overview

Dopemux now supports multiple workspaces with complete data isolation. This guide helps you migrate your existing single-workspace setup to multi-workspace.

## What's New

### Added Features
- ✅ Per-workspace cognitive state tracking
- ✅ Isolated knowledge graphs per workspace
- ✅ Cross-workspace queries and aggregation
- ✅ Workspace switching with context preservation
- ✅ Visual workspace indicator in statusline

### Breaking Changes
**None!** Multi-workspace is fully backward compatible.

## Migration Steps

### 1. Update Environment Variables

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Set your default workspace (your main project)
export DEFAULT_WORKSPACE_PATH=~/code/dopemux-mvp

# Optional: List additional workspaces for cross-queries
export WORKSPACE_PATHS=~/code/project1,~/code/project2

# Optional: Enable workspace features (default: true)
export ENABLE_WORKSPACE_ISOLATION=true
export ENABLE_CROSS_WORKSPACE_QUERIES=true
```

Reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### 2. Update .env.example

Copy the new workspace variables from `.env.example`:

```bash
# Multi-Workspace Support
DEFAULT_WORKSPACE_PATH=~/code/dopemux-mvp
WORKSPACE_PATHS=
ENABLE_WORKSPACE_ISOLATION=true
ENABLE_CROSS_WORKSPACE_QUERIES=true
WORKSPACE_CACHE_TTL=3600
```

### 3. Database Migration (Automatic)

Database migrations run automatically on service startup. Existing data is preserved and associated with your default workspace.

**To verify migration:**
```bash
# Check database has workspace indexes
dopemux doctor --check-database

# Verify existing data migrated correctly
dopemux query decisions --workspace ~/code/dopemux-mvp | head -5
```

### 4. Update Scripts (Optional)

If you have custom scripts using Dopemux APIs:

**Before (single workspace):**
```python
client = DopemuxClient()
state = await client.get_adhd_state()
```

**After (multi-workspace aware):**
```python
# Auto-detect workspace from current directory
client = DopemuxClient()
state = await client.get_adhd_state()

# Or explicitly specify workspace
client = DopemuxClient(workspace_path="~/code/my-project")
state = await client.get_adhd_state()
```

### 5. Update MCP Configuration (Optional)

If using custom MCP server configurations, add workspace support:

**~/.claude/settings.json:**
```json
{
  "mcpServers": {
    "serena": {
      "command": "python",
      "args": ["-m", "serena.v2.mcp_server"],
      "env": {
        "WORKSPACE_PATH": "${workspaceFolder}"
      }
    }
  }
}
```

### 6. Test Multi-Workspace Setup

Verify everything works:

```bash
# Check workspace detection
dopemux workspace detect
# Should show: Current Workspace: /Users/you/code/dopemux-mvp

# Test workspace switching
cd ~/code/another-project
dopemux workspace detect
# Should show: Current Workspace: /Users/you/code/another-project

# Test cross-workspace query
dopemux query decisions --all-workspaces "authentication"
```

## Existing Data Handling

### Where is my existing data?

All existing data is automatically associated with your `DEFAULT_WORKSPACE_PATH`. Nothing is lost!

**Data migration summary:**
- Cognitive state → Associated with default workspace
- Decisions → Tagged with default workspace
- Session history → Moved to default workspace
- ADHD metrics → Scoped to default workspace

### Can I split existing data across workspaces?

Yes! Use the data migration tool:

```bash
# Preview what would be migrated
dopemux migrate preview \
  --from ~/code/dopemux-mvp \
  --to ~/code/new-project \
  --filter "decisions after 2025-01-01"

# Perform migration
dopemux migrate execute \
  --from ~/code/dopemux-mvp \
  --to ~/code/new-project \
  --filter "decisions after 2025-01-01" \
  --copy  # Use --move to remove from source
```

## Troubleshooting

### Issue: Workspace not detected

**Symptom:** `dopemux workspace detect` shows wrong workspace

**Solution:**
```bash
# Set explicit workspace
export DEFAULT_WORKSPACE_PATH=/full/path/to/workspace

# Or use --workspace flag
dopemux --workspace ~/code/my-project start
```

### Issue: Data showing in wrong workspace

**Symptom:** Decisions from one project appear in another

**Solution:**
```bash
# Check data isolation
dopemux doctor --check-isolation

# Re-migrate if needed
dopemux migrate reset ~/code/my-project
```

### Issue: Cross-workspace queries not working

**Symptom:** `--all-workspaces` returns no results

**Solution:**
```bash
# Verify workspace paths configured
echo $WORKSPACE_PATHS

# Check each workspace has data
dopemux query decisions --workspace ~/code/project1
dopemux query decisions --workspace ~/code/project2
```

### Issue: Performance degradation

**Symptom:** Queries slower after migration

**Solution:**
```bash
# Rebuild workspace indexes
dopemux maintain rebuild-indexes

# Verify indexes exist
dopemux doctor --check-indexes

# Clear and rebuild cache
dopemux cache clear --all
```

## Rollback Instructions

If you need to revert to single-workspace:

```bash
# 1. Remove workspace environment variables
# Edit ~/.zshrc and remove DEFAULT_WORKSPACE_PATH, etc.

# 2. Restart services
dopemux restart --all

# 3. (Optional) Consolidate all workspaces to one
dopemux migrate consolidate \
  --target ~/code/main-workspace \
  --sources ~/code/p1,~/code/p2
```

## Performance Comparison

**Before (single workspace):**
- Query time: ~40ms
- Cache efficiency: 85%

**After (multi-workspace):**
- Single workspace query: ~45ms (+5ms)
- Multi-workspace query (3 workspaces): ~180ms
- Cache efficiency: 88% (+3% due to workspace scoping)

**Impact:** Negligible for single workspace, excellent for multi-workspace.

## Best Practices Post-Migration

### ✅ Do:
- Use `DEFAULT_WORKSPACE_PATH` for your main project
- Add frequently-used projects to `WORKSPACE_PATHS`
- Check workspace before making changes (`dopemux workspace status`)
- Leverage cross-workspace queries for insights

### ❌ Don't:
- Manually edit workspace_path in database (use migration tools)
- Share `.dopemux/` directories between workspaces
- Mix workspace data without using proper migration tools

## Support

Having trouble migrating?

- Check [Troubleshooting Guide](docs/troubleshooting/workspaces.md)
- Run diagnostics: `dopemux doctor --verbose`
- Report issues: https://github.com/dopemux/dopemux-mvp/issues

## Next Steps

After migration, explore multi-workspace features:

1. [Multi-Workspace Usage Guide](README.md#multi-workspace-usage)
1. [Workspace API Reference](docs/api/workspace.md)
1. [Advanced Workspace Patterns](docs/advanced/workspace-patterns.md)

---

**Migration Complete!** 🎉

Your Dopemux installation now supports multiple workspaces with full isolation and cross-workspace intelligence.
