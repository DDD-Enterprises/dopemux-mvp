---
id: DEVELOPMENT_SETUP
title: Development Setup - Quick Start
type: how-to
owner: '@hu3mann'
date: '2026-02-02'
tags:
- development
- dev-mode
- contributing
- setup
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
prelude: Development Setup - Quick Start (how-to) for dopemux documentation and developer
  workflows.
---
# Dopemux Development Setup - 5 Minute Quick Start

**Goal**: Get you coding on Dopemux in 5-10 minutes
**Audience**: New contributors, MCP developers, Dopemux core developers

---

## 🎯 Three Development Scenarios

Choose your path:

| Scenario | You Want To... | Time to Setup |
|----------|----------------|---------------|
| **[Zen MCP Development](#zen-mcp-development)** | Improve thinkdeep, planner, consensus tools | 5 minutes |
| **[Dopemux Core Development](#dopemux-core-development)** | Work on CLI, profiles, commands | 3 minutes |
| **[MCP Server Development](#mcp-server-development)** | Develop any MCP server (Serena, ConPort, etc.) | 5-10 minutes |

---

## 🚀 Zen MCP Development

**Goal**: Fork Zen MCP, develop locally, Dopemux auto-uses your version

### Setup (5 minutes)

```bash
# 1. Fork zen-mcp-server on GitHub (when extracted as separate repo)
# For now, Zen is embedded in dopemux-mvp

# 2. Clone Dopemux if you haven't
git clone https://github.com/YOUR_USER/dopemux-mvp.git ~/code/dopemux-mvp
cd ~/code/dopemux-mvp

# 3. Install in editable mode
pip install -e ".[dev]"

# 4. Verify dev mode detected
dopemux dev status
# Should show: "✅ ACTIVE" and "zen: /path/to/dopemux-mvp ✅"
```

### Development Workflow

```bash
# 1. Edit Zen tools
cd ~/code/dopemux-mvp
nano docker/mcp-servers/zen/zen-mcp-server/tools/thinkdeep.py

# 2. Test changes immediately
# Restart dopemux or Claude Code to reload
dopemux restart

# 3. Your changes are now active!
# Test in Claude Code with /zen:thinkdeep

# 4. Commit when ready
git checkout -b feature/improve-thinkdeep
git commit -m "feat(zen): improve hypothesis tracking"
git push origin feature/improve-thinkdeep
# Create PR
```

---

## 💻 Dopemux Core Development

**Goal**: Work on dopemux CLI, profile system, ConPort commands

### Setup (3 minutes)

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USER/dopemux-mvp.git ~/code/dopemux-mvp
cd ~/code/dopemux-mvp
pip install -e ".[dev]"

# 2. Verify installation
dopemux --version
dopemux dev status
# Should show: "✅ ACTIVE" with pyproject.toml detection
```

### Development Workflow

```bash
# 1. Edit Dopemux code
nano src/dopemux/commands/decisions_commands.py
nano src/dopemux/profile_manager.py

# 2. Test immediately (no reinstall needed!)
dopemux decisions stats
dopemux profile list

# 3. Run tests
pytest tests/ -v

# 4. Commit
git commit -m "feat: add decision filtering by energy"
```

**Key Benefit**: Editable install means changes take effect immediately!

---

## 🔧 MCP Server Development

**Goal**: Develop any MCP server with auto-detection

### Setup (5-10 minutes)

```bash
# Example: Working on Serena LSP

# 1. Fork and clone to standard location
git clone git@github.com:YOUR_USER/serena-lsp.git ~/code/serena-lsp
cd ~/code/serena-lsp

# 2. Install in editable mode
pip install -e ".[dev]"

# 3. Verify Dopemux detects it
cd ~/code/dopemux-mvp
dopemux dev status
# Should show: "serena: ~/code/serena-lsp ✅"
```

### Development Workflow

```bash
# 1. Edit MCP server code
cd ~/code/serena-lsp
nano serena/navigation.py

# 2. Restart to reload
dopemux restart

# 3. Test changes
# Use MCP tools in Claude Code

# 4. Commit
git commit -m "feat: improve symbol search"
```

---

## ✅ Verification Checklist

After setup, verify dev mode is working:

```bash
# 1. Check dev mode status
dopemux dev status

# Expected output:
# ✅ Dev Mode: ACTIVE
# ✅ Test Databases: Enabled
# ✅ Log Level: DEBUG
# ✅ Component paths detected

# 2. Check detected paths
dopemux dev paths

# Should show components with local checkouts

# 3. Test a change
# Edit a file → Restart → Verify change works
```

---

## 🎛️ Dev Mode Features

### Automatic Detection

Dev mode activates automatically when:

1. **Environment variable set**: `export DOPEMUX_DEV_MODE=true`
2. **Inside Dopemux repo**: Has `pyproject.toml` + `src/dopemux/`
3. **Component in standard location**: `~/code/zen-mcp-server` exists

### Standard Development Locations

Dev mode checks these paths (in order):

| Component | Paths Checked |
|-----------|---------------|
| **Zen MCP** | `~/code/zen-mcp-server`, `~/zen-mcp-server`, `$ZEN_DEV_PATH` |
| **ConPort** | `~/code/conport-mcp`, `~/conport-mcp`, `$CONPORT_DEV_PATH` |
| **Serena** | `~/code/serena-lsp`, `~/serena-lsp`, `$SERENA_DEV_PATH` |

### Test Database Isolation

**Production databases**: `~/.dopemux/databases/conport.db`
**Dev databases**: `~/.dopemux/dev/databases/conport-test.db`

**Why?**
- Safe experimentation (don't corrupt your real data)
- Easy reset (just delete test database)
- No production pollution with test decisions

### Debug Logging

Dev mode automatically enables `DEBUG` logging:
- See every operation
- Helpful for debugging
- Filter with `grep` if too noisy

### Service Skipping

Skip heavy services for faster iteration:

```bash
export DOPEMUX_SKIP_SERVICES="leantime,task-master,milvus"
dopemux start
# Only starts: zen, conport, serena (core dev stack)
```

---

## ⚙️ Configuration

### Enable Dev Mode Globally

```bash
# Add to ~/.bashrc or ~/.zshrc
export DOPEMUX_DEV_MODE=true

# Or use convenience command
dopemux dev enable
# Adds to shell profile automatically
```

### Custom Component Paths

```bash
# Override default paths
export ZEN_DEV_PATH=~/projects/my-zen-fork
export CONPORT_DEV_PATH=/custom/path/conport

# Verify
dopemux dev paths
```

### Configure Skipped Services

```bash
# Skip services you don't need
export DOPEMUX_SKIP_SERVICES="leantime,milvus,task-master"

# Start with minimal stack
dopemux start
```

---

## 🎯 Understanding Dev Mode Tradeoffs

### Production vs Dev Mode Comparison

| Feature | Production | Dev Mode | Impact |
|---------|-----------|----------|--------|
| **Component Paths** | Installed packages | Local checkouts | ✅ Edit code directly |
| **Databases** | Production data | Test databases | ✅ Safe experimentation |
| **Logging** | INFO | DEBUG | ⚠️ Verbose but helpful |
| **Services** | All running | Core only | ✅ Faster startup (10s vs 60s) |
| **Resources** | 8GB RAM | 2GB RAM | ✅ Lower requirements |
| **Realism** | Full integration | Minimal services | ⚠️ May miss integration bugs |

### When to Use Each Mode

**Use Dev Mode For:**
- ✅ Developing features
- ✅ Testing changes quickly
- ✅ Learning the codebase
- ✅ Safe experimentation

**Use Production Mode For:**
- ✅ Integration testing
- ✅ Performance testing
- ✅ Full system validation
- ✅ Real work sessions

### Key Tradeoffs Explained

#### 1. Isolation vs Realism

**Dev Mode**: Uses test databases, minimal services
- **Benefit**: Safe, fast, focused
- **Cost**: May not catch production-specific bugs
- **Recommendation**: Use dev mode for development, test production-like before merging

#### 2. Auto-Detection vs Explicit Configuration

**Dev Mode**: Automatically detects `~/code/zen-mcp-server`
- **Benefit**: Zero-config for 90% of users
- **Cost**: May activate unexpectedly
- **Recommendation**: Run `dopemux dev status` to verify state

#### 3. Debug Logging vs Performance

**Dev Mode**: Full DEBUG logging
- **Benefit**: See everything, easier debugging
- **Cost**: ~20% performance overhead, log files grow quickly
- **Recommendation**: Use grep/filtering to reduce noise

#### 4. Test Databases vs Production Data

**Dev Mode**: Test databases (empty or with fixtures)
- **Benefit**: Can't corrupt your real data
- **Cost**: Can't test against real data scenarios
- **Recommendation**: Never allow writes to production in dev mode

### Common Pitfalls

❌ **Mistake**: Forgetting you're in dev mode, wondering why data disappeared
✅ **Solution**: Check `dopemux dev status` - shows database locations

❌ **Mistake**: Testing against production data in dev mode
✅ **Solution**: Dev mode enforces test database isolation

❌ **Mistake**: Committing with skipped services, missing integration issues
✅ **Solution**: Run full stack before merging: `unset DOPEMUX_SKIP_SERVICES`

---

## 🔧 Troubleshooting

### Dev Mode Not Detected

```bash
# Check status
dopemux dev status
# Output: "❌ Inactive"

# Solution 1: Enable explicitly
export DOPEMUX_DEV_MODE=true
dopemux dev status

# Solution 2: Clone to standard location
git clone ... ~/code/zen-mcp-server
dopemux dev paths

# Solution 3: Use env var override
export ZEN_DEV_PATH=/custom/path/zen
```

### Changes Not Taking Effect

```bash
# 1. Verify dev mode active
dopemux dev status

# 2. Restart Dopemux
dopemux restart

# 3. Check which path is being used
dopemux dev paths

# 4. Verify editable install
pip show dopemux
# Should show: Location: /path/to/dopemux-mvp/src
```

### Test Database Not Used

```bash
# Verify test database setting
dopemux dev status
# Should show: "Test Databases: ✅"

# Check database path
ls ~/.dopemux/dev/databases/

# Force test database
export DOPEMUX_USE_TEST_DB=true
```

### Too Much Debug Output

```bash
# Reduce noise with grep
dopemux start 2>&1 | grep -v "DEBUG"

# Or temporarily disable debug
export LOG_LEVEL=INFO
dopemux start
```

---

## 📚 Next Steps

### Documentation Links

- **For Zen Contributors**: [DEVELOPING_ZEN.md](./DEVELOPING_ZEN.md) - Zen-specific guide
- **For Core Contributors**: [DEVELOPING_DOPEMUX_CORE.md](./DEVELOPING_DOPEMUX_CORE.md) - Core development guide
- **For Troubleshooting**: [development-troubleshooting.md](./development-troubleshooting.md) - Common issues

### Learning Resources

- **Design Document**: [dev-mode-design.md](../04-explanation/design-decisions/dev-mode-design.md) - Complete technical spec
- **Architecture**: [system-bible.md](../94-architecture/system-bible.md) - System architecture overview
- **MCP Servers**: [MCP Documentation](../03-reference/services/) - Individual MCP server docs

### Getting Help

- **Check status first**: `dopemux dev status`
- **View logs**: `dopemux health --verbose`
- **GitHub Issues**: Report bugs or ask questions
- **Community**: Join contributor discussions

---

## 🎯 Quick Reference Commands

```bash
# Dev Mode Management
dopemux dev status          # Show dev mode status
dopemux dev enable          # Enable dev mode globally
dopemux dev paths           # Show detected component paths

# Development Workflow
pip install -e ".[dev]"     # Editable install for live changes
dopemux restart             # Reload after code changes
pytest tests/ -v            # Run tests

# Verification
dopemux --version           # Check installation
dopemux health              # System health check
git status                  # Check uncommitted changes
```

---

**Time to Productivity**: 5-10 minutes from clone to first change
**Developer Experience**: Auto-detection, test isolation, instant feedback
**Safety**: Test databases prevent production data corruption
