---
id: HARDCODED_PATHS_AUDIT
title: Hardcoded_Paths_Audit
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Hardcoded_Paths_Audit (explanation) for dopemux documentation and developer
  workflows.
---
# Hardcoded Paths Audit - Multi-User Transformation

**Created**: 2025-10-18
**Purpose**: Document all hardcoded paths that prevent multi-user deployment
**Status**: Analysis Complete

---

## 📊 Summary

**Total Occurrences**: 18,333 (mostly in `.venv`, `.git`, `node_modules`)
**Files Requiring Changes**: ~30 production files
**Priority**: HIGH - Blocks multi-user adoption

---

## 🎯 Critical Files Needing Updates

### **Category 1: Core Infrastructure** (CRITICAL)

**docker/mcp-servers/docker-compose.yml**
- Purpose: MCP server orchestration
- Hardcoded: Volume mounts, network names
- Fix: Use env vars `${DOPEMUX_HOME}` and `${DOPEMUX_WORKSPACE}`

**.claude.json**
- Purpose: Claude Code MCP configuration
- Hardcoded: `/Users/hue/code/dopemux-mvp/docker/mcp-servers/zen/zen-mcp-server`
- Fix: Generate from template with `~/.dopemux` and workspace detection

**config/docs/enforcement.yaml**
- Purpose: Documentation linting rules
- Hardcoded: File paths
- Fix: Use relative paths from workspace root

---

### **Category 2: Scripts & Automation** (HIGH PRIORITY)

**Scripts with `/Users/hue` (30 files):**

1. `scripts/mcp-wrappers/*.sh` - MCP server wrappers
   - Fix: Use `$HOME/.dopemux` instead of `/Users/hue`

2. `scripts/migration/*.py` - Database migration scripts
   - Fix: Accept workspace path as CLI argument

3. `scripts/setup-leantime-env.sh` - Leantime setup
   - Fix: Use `DOPEMUX_HOME` env var

4. `scripts/deploy_serena_complete_system.py` - Serena deployment
   - Fix: Detect workspace via git or pass as arg

5. `integration/claude-code/install-dopemux-claude.sh` - Claude Code integration
   - Fix: Template-based generation

---

### **Category 3: MCP Server Configs** (MEDIUM)

**docker/mcp-servers/conport/instance_detector.py**
- Purpose: Detect running dopemux instances
- Hardcoded: Workspace paths
- Fix: Use workspace detection function

**docker/mcp-servers/*/Dockerfile**
- Purpose: Build MCP containers
- Hardcoded: Some have `/app` paths (OK - internal to container)
- Fix: None needed (container-internal paths are fine)

---

### **Category 4: Examples & Tests** (LOW - Can stay as examples)

**examples/*.py** - Example scripts
- Fix: Add comments "# Example - update path to your workspace"
- Or: Use `os.getcwd()` for dynamic paths

**tests/*.py** - Test fixtures
- Fix: Use temp directories or `pytest.fixtures` with dynamic paths

---

## 🔧 Replacement Strategy

### **Pattern 1: User Home Directory**
```python
# Before:
workspace = "/Users/hue/code/dopemux-mvp"

# After:
workspace = os.path.expanduser("~/.dopemux")
# Or from env:
workspace = os.getenv("DOPEMUX_HOME", os.path.expanduser("~/.dopemux"))
```

### **Pattern 2: Project Workspace**
```python
# Before:
workspace_id = "/Users/hue/code/dopemux-mvp"

# After:
workspace_id = detect_workspace()  # Uses git rev-parse --show-toplevel

# Or from env (dopemux start sets this):
workspace_id = os.getenv("DOPEMUX_WORKSPACE_ROOT")
```

### **Pattern 3: Docker Volumes**
```yaml
# Before:
volumes:
  - /Users/hue/code/dopemux-mvp:/app

# After:
volumes:
  - ${DOPEMUX_WORKSPACE}:/app

# Or for shared data:
  - ${DOPEMUX_HOME}/databases:/data
```

### **Pattern 4: MCP Server Paths**
```json
// Before (.claude.json):
"cwd": "/Users/hue/code/dopemux-mvp/docker/mcp-servers/zen/zen-mcp-server"

// After (template):
"cwd": "${DOPEMUX_WORKSPACE}/docker/mcp-servers/zen/zen-mcp-server"

// Or with submodule:
"cwd": "${DOPEMUX_WORKSPACE}/external/zen-mcp-server"
```

---

## 📁 New Environment Variables Required

```bash
# Global dopemux home (for shared resources)
DOPEMUX_HOME=~/.dopemux

# Current project workspace (set by dopemux start)
DOPEMUX_WORKSPACE_ROOT=$(git rev-parse --show-toplevel)

# Zen dev mode override (optional)
ZEN_DEV_PATH=~/code/zen-mcp-server  # If exists, use this instead of submodule
```

---

## 🔄 Migration Process

### **Phase 1: Create Template System**
1. Create `.env.template` with `${DOPEMUX_HOME}` placeholders
2. Create `.claude.json.template` with variable substitution
3. Create `docker-compose.template.yml` with env var placeholders

### **Phase 2: Update All Scripts**
1. Replace hardcoded paths with env vars
2. Add workspace detection functions
3. Use `~/.dopemux` for global resources
4. Use detected workspace for project-specific resources

### **Phase 3: Generate Configs on Setup**
1. `scripts/setup.sh` creates `~/.dopemux/`
2. `dopemux init` generates `.dopemux/` in project
3. Both substitute env vars into templates
4. Validation checks all paths exist

---

## ✅ Validation Checklist

After transformation, verify:

- [ ] No `/Users/hue` remains in production code (examples/docs OK)
- [ ] All paths use env vars or workspace detection
- [ ] `scripts/setup.sh` works on fresh machine
- [ ] `dopemux init` works in any directory
- [ ] Docker services start with env var paths
- [ ] MCP servers connect with generated configs
- [ ] Multi-project mode works (2+ projects simultaneously)

---

## 🎯 Priority Order

### **Critical (Do First):**
1. `.claude.json` template system
2. `docker-compose.yml` env var substitution
3. Workspace detection in core CLI
4. MCP wrapper scripts

### **High (Do Soon):**
1. Migration scripts parameterization
2. Setup automation scripts
3. Example scripts documentation

### **Low (Can Defer):**
1. Test fixtures (use temp dirs)
2. Old backup scripts
3. One-off deployment scripts

---

## 📊 Estimated Impact

**Files Modified**: ~30 production files
**Lines Changed**: ~200-300 lines (mostly find-replace)
**Time Required**: 2-3 hours (with current 17.6x velocity: **~10 minutes!**)
**Risk**: LOW (mostly path substitution, easily testable)

---

**Next Step**: Start with `.claude.json` template and workspace detection
 minutes!**)
**Risk**: LOW (mostly path substitution, easily testable)

---

**Next Step**: Start with `.claude.json` template and workspace detection
