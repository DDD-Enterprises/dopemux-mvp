# Dopemux Claude Configuration Documentation

This directory contains documentation and templates for Dopemux MCP servers and Claude Code configuration.

## MCP Server Documentation

These files document each MCP server's capabilities, tools, and usage patterns:

- **`MCP_DopeContext.md`** - Semantic code & docs search (v2.0 - Structure-Aware Chunking)
- **`MCP_Zen.md`** - Multi-model reasoning suite (thinkdeep, planner, consensus, debug, codereview)
- **`MCP_ConPort.md`** - Context & knowledge graph (decisions, progress, patterns)
- **`MCP_Serena.md`** - Semantic code intelligence (LSP, navigation, complexity)
- **`MCP_Exa.md`** - Neural search engine (fast web search)
- **`MCP_GPTResearcher.md`** - Deep research engine (comprehensive multi-source)
- **`MCP_DesktopCommander.md`** - Desktop automation and control

## Installation

### First-Time Setup

**Copy MCP docs to global Claude config**:
```bash
# The global .claude directory is in your home directory
cp .claude/docs/MCP_*.md ~/.claude/
```

**Purpose**: These docs are loaded by Claude Code as global instructions, teaching Claude about each MCP server's capabilities and usage patterns.

### Updating Docs

When MCP capabilities change:

1. **Update global version**:
   ```bash
   # Edit the global file directly
   vim ~/.claude/MCP_DopeContext.md
   ```

2. **Copy back to repo for version control**:
   ```bash
   # Keep repo in sync
   cp ~/.claude/MCP_*.md .claude/docs/
   git add .claude/docs/MCP_*.md
   git commit -m "docs: Update MCP documentation"
   ```

3. **Or update repo first, then copy to global**:
   ```bash
   # Edit repo version
   vim .claude/docs/MCP_DopeContext.md

   # Copy to global
   cp .claude/docs/MCP_*.md ~/.claude/
   ```

### Why Both Locations?

**Global (`~/.claude/`):**
- Used by Claude Code at runtime
- Teaches Claude about MCP capabilities
- Loaded for ALL projects automatically
- User-specific configuration

**Repo (`.claude/docs/`):**
- Version controlled
- Team collaboration
- Installation source
- Reference documentation
- Can be shared/copied

## Structure

```
.claude/
├── docs/                          # Documentation (this directory)
│   ├── README.md                  # This file
│   ├── MCP_DopeContext.md         # Dope-Context MCP docs
│   ├── MCP_Zen.md                 # Zen MCP docs
│   ├── MCP_ConPort.md             # ConPort MCP docs
│   ├── MCP_Serena.md              # Serena MCP docs
│   ├── MCP_Exa.md                 # Exa MCP docs
│   ├── MCP_GPTResearcher.md       # GPT-Researcher MCP docs
│   ├── MCP_DesktopCommander.md    # Desktop Commander MCP docs
│   ├── GLOBAL_MCP_CONFIGURATION.md # Global config strategy
│   └── STATUSLINE*.md             # Status line docs
│
├── CLAUDE.md                      # Project-specific instructions
├── WORKTREE_MCP_SETUP.md         # Worktree configuration guide
└── agents/                        # Custom agent definitions
    ├── architect.md
    ├── researcher.md
    └── ...
```

## Recent Updates

### 2025-10-23: Dope-Context v2.0 Optimization
- ✅ Structure-aware markdown chunking (+30-40% relevance)
- ✅ Autonomous docs indexing (zero-touch operation)
- ✅ Complexity scoring for docs (ADHD cognitive load)
- ✅ Hierarchy preservation (complete sections)
- ✅ Enhanced metadata (section_hierarchy, parent_section, etc.)

**Updated file**: `MCP_DopeContext.md`
**Commits**: b3a08d7b, ac4ca55d
**Impact**: 2-3x better docs search

### 2025-10-16: Global MCP Configuration
- Migrated all MCP servers to global `~/.claude.json`
- Eliminated per-project duplication
- Auto-works in all worktrees

**Documentation**: `GLOBAL_MCP_CONFIGURATION.md`

## Best Practices

### Keeping Docs in Sync

**Option 1: Repo First (Recommended)**
```bash
# 1. Update repo version
vim .claude/docs/MCP_DopeContext.md

# 2. Copy to global
cp .claude/docs/MCP_DopeContext.md ~/.claude/

# 3. Commit
git add .claude/docs/MCP_DopeContext.md
git commit -m "docs: Update Dope-Context MCP documentation"
```

**Option 2: Global First**
```bash
# 1. Update global directly
vim ~/.claude/MCP_DopeContext.md

# 2. Copy to repo
cp ~/.claude/MCP_DopeContext.md .claude/docs/

# 3. Commit
git add .claude/docs/MCP_DopeContext.md
git commit -m "docs: Update Dope-Context MCP documentation"
```

### For New Team Members

```bash
# Clone repo
git clone https://github.com/DDD-Enterprises/dopemux-mvp.git
cd dopemux-mvp

# Copy MCP docs to global config
cp .claude/docs/MCP_*.md ~/.claude/

# Done! All MCP servers documented and ready to use
```

## Notes

- Global `.claude.json` contains actual MCP server configurations (commands, args)
- These `.md` files contain documentation and usage instructions
- Claude reads both at runtime to understand capabilities
- Keep both repo and global copies in sync for consistency

---

**Last Updated**: 2025-10-23
**Version**: Dope-Context v2.0, Zen v9.0, ConPort v2.0
