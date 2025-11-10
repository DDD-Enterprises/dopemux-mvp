---
id: DEV_MODE_DESIGN
title: Dev_Mode_Design
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Dopemux Dev Mode - Comprehensive Design

**Created**: 2025-10-18
**Purpose**: Enable development on dopemux core, Zen MCP, and other MCP servers
**Status**: Design Complete, Ready for Implementation

---

## 🎯 Dev Mode Goals

**Three Development Scenarios**:

1. **Zen MCP Development** - Work on thinkdeep, planner, consensus, codereview
2. **Dopemux Core Development** - Improve CLI, profile system, ConPort commands
3. **MCP Server Development** - Develop any MCP server (Serena, ConPort, etc.)

**Key Requirements**:
- Auto-detect local development checkouts
- Hot reload when code changes
- Test databases (don't pollute production data)
- Debug logging enabled
- Fast iteration (skip unnecessary services)
- Easy contribution workflow

---

## 🔧 Implementation Design

### **1. Zen MCP Dev Mode** (For Contributors)

**Goal**: Fork zen-mcp-server, develop locally, dopemux auto-uses your version

**Setup Workflow**:
```bash
# 1. Fork zen-mcp-server on GitHub
# (Future: after Zen extracted as submodule)

# 2. Clone to standard location
git clone git@github.com:YOUR_USER/zen-mcp-server.git ~/code/zen-mcp-server
cd ~/code/zen-mcp-server

# 3. Install in editable mode
pip install -e ".[dev]"

# 4. Dopemux auto-detects!
cd ~/any-project
dopemux start
# → Uses ~/code/zen-mcp-server instead of submodule
# → Shows: "🔧 Zen DEV MODE: Using ~/code/zen-mcp-server"
```

**Detection Logic** (in dopemux start):
```python
def detect_zen_path():
    """Detect Zen MCP path with dev mode priority."""
    candidates = [
        Path("~/code/zen-mcp-server").expanduser(),          # Dev mode (highest priority)
        Path("~/zen-mcp-server").expanduser(),              # Alternative dev location
        Path(os.getenv("ZEN_DEV_PATH")).expanduser() if os.getenv("ZEN_DEV_PATH") else None,  # Env override
        Path("external/zen-mcp-server"),                    # Submodule (production)
        Path("docker/mcp-servers/zen/zen-mcp-server"),     # Legacy embedded
    ]

    for path in candidates:
        if path and path.exists() and (path / "server.py").exists():
            if "code/zen-mcp-server" in str(path):
                console.print(f"[yellow]🔧 Zen DEV MODE: {path}[/yellow]")
            return path

    raise FileNotFoundError("Zen MCP not found. Run: git submodule update --init")

# Use in .claude.json generation:
zen_path = detect_zen_path()
claude_config["mcpServers"]["zen"]["cwd"] = str(zen_path)
```

**Development Workflow**:
```bash
# Work on Zen thinkdeep tool
cd ~/code/zen-mcp-server
nano tools/thinkdeep.py

# Test changes immediately
cd ~/test-project
dopemux start
# Uses your modified Zen!

# Commit when ready
git checkout -b feature/improve-thinkdeep
git commit -m "feat: improve hypothesis tracking in thinkdeep"
git push origin feature/improve-thinkdeep
# Create PR to zen-mcp-server repo
```

**Hot Reload**:
```bash
# Option 1: Restart dopemux (quick)
dopemux restart

# Option 2: Just restart Zen MCP
# (Future: dopemux reload zen)

# Option 3: Zen watches for changes (if implemented)
# Zen auto-reloads on .py file changes
```

---

### **2. Dopemux Core Dev Mode** (For Core Contributors)

**Goal**: Work on dopemux CLI, profile system, ConPort commands, etc.

**Setup** (Already Works!):
```bash
git clone https://github.com/YOUR_USER/dopemux-mvp.git
cd dopemux-mvp
pip install -e ".[dev]"
```

**Development Workflow**:
```bash
# Edit dopemux code
nano src/dopemux/profile_manager.py
nano src/dopemux/commands/decisions_commands.py

# Test immediately (no reinstall needed!)
dopemux profile list          # Uses your edited code
dopemux decisions stats       # Live changes

# Run tests
pytest tests/

# Commit
git commit -m "feat: improve profile merge algorithm"
```

**Dev Mode Enhancements Needed**:

**A. Test Database Isolation**:
```python
# Detect dev mode
if os.getenv("DOPEMUX_DEV_MODE") == "true":
    # Use test databases, not production
    CONPORT_DB = "~/.dopemux/dev/databases/conport-test.db"
    console.print("[yellow]🔧 DEV MODE: Using test databases[/yellow]")

# Or auto-detect:
if Path("pyproject.toml").exists() and Path("src/dopemux").exists():
    # We're IN dopemux repo, use dev databases
    DEV_MODE = True
```

**B. Debug Logging**:
```python
if os.getenv("DOPEMUX_DEV_MODE") == "true":
    logging.basicConfig(level=logging.DEBUG)
    console.print("[dim]Debug logging enabled[/dim]")
```

**C. Skip Services**:
```bash
# Dev mode skips heavy services for faster iteration
export DOPEMUX_DEV_MODE=true
export DOPEMUX_SKIP_SERVICES="leantime,task-master,milvus"

dopemux start
# Only starts: zen, conport, serena (core dev stack)
```

---

### **3. MCP Server Dev Mode** (For MCP Contributors)

**Goal**: Develop any MCP server with hot reload

**Pattern** (Similar to Zen):
```bash
# Example: Working on ConPort MCP
git clone git@github.com:YOUR_USER/conport-mcp.git ~/code/conport-mcp
cd ~/code/conport-mcp
pip install -e ".[dev]"

# Dopemux detection (in docker-compose.yml or startup):
if [ -d ~/code/conport-mcp ]; then
    # Dev mode: use local checkout
    CONPORT_PATH=~/code/conport-mcp
    echo "🔧 ConPort DEV MODE"
else
    # Production: use docker container
    CONPORT_PATH=docker://mcp-conport
fi
```

**Volume Mounts for Dev Mode**:
```yaml
# docker-compose.yml (conditional)
services:
  conport:
    volumes:
      # Production: use container code
      - ${CONPORT_DEV_PATH:-./docker/mcp-servers/conport}:/app

      # If CONPORT_DEV_PATH set, mount local checkout
      # → Live code editing with hot reload!
```

---

## 🎛️ Dev Mode Configuration

### **Environment Variables**:

```bash
# ~/.dopemux/dev.env (sourced in dev mode)

# Global dev mode toggle
DOPEMUX_DEV_MODE=true

# Component dev paths (optional - auto-detected if not set)
ZEN_DEV_PATH=~/code/zen-mcp-server
CONPORT_DEV_PATH=~/code/conport-mcp
SERENA_DEV_PATH=~/code/serena-lsp

# Skip services for faster iteration
DOPEMUX_SKIP_SERVICES=leantime,task-master,milvus,metamcp

# Debug settings
LOG_LEVEL=DEBUG
ENABLE_HOT_RELOAD=true

# Test databases (isolated from production)
USE_TEST_DATABASES=true
```

### **Dev Mode Detection**:

```python
# src/dopemux/dev_mode.py

import os
from pathlib import Path

class DevMode:
    """Detects and manages dev mode settings."""

    @staticmethod
    def is_active() -> bool:
        """Check if dev mode is active."""
        # Explicit env var
        if os.getenv("DOPEMUX_DEV_MODE") == "true":
            return True

        # Auto-detect: inside dopemux repo?
        if (Path("pyproject.toml").exists() and
            (Path("src/dopemux").exists() or Path("docker/mcp-servers").exists())):
            return True

        return False

    @staticmethod
    def get_component_path(component: str) -> Optional[Path]:
        """Get dev path for component if available."""
        # Check env var first
        env_var = f"{component.upper()}_DEV_PATH"
        if os.getenv(env_var):
            return Path(os.getenv(env_var)).expanduser()

        # Check standard locations
        standard_paths = {
            "zen": [
                "~/code/zen-mcp-server",
                "~/zen-mcp-server",
                "~/dev/zen-mcp-server"
            ],
            "conport": [
                "~/code/conport-mcp",
                "~/conport-mcp"
            ],
            "serena": [
                "~/code/serena-lsp",
                "~/serena-lsp"
            ]
        }

        for path_str in standard_paths.get(component, []):
            path = Path(path_str).expanduser()
            if path.exists():
                return path

        return None
```

---

## 🚀 Implementation Plan

### **Phase 1: Core Dev Mode** (~30 min)

**A. Create DevMode class**:
```python
# src/dopemux/dev_mode.py
class DevMode:
    @staticmethod
    def is_active() -> bool
    @staticmethod
    def get_component_path(component) -> Optional[Path]
    @staticmethod
    def use_test_databases() -> bool
    @staticmethod
    def get_log_level() -> str
```

**B. Integrate into dopemux start**:
```python
# In launcher.py or cli.py start command:
if DevMode.is_active():
    console.print("[yellow]🔧 DEV MODE ACTIVE[/yellow]")
    console.print(f"  Log level: {DevMode.get_log_level()}")
    console.print(f"  Test databases: {DevMode.use_test_databases()}")

    # Show detected dev paths
    for component in ["zen", "conport", "serena"]:
        dev_path = DevMode.get_component_path(component)
        if dev_path:
            console.print(f"  {component}: {dev_path}")
```

**C. CLI Command**:
```bash
# New command
dopemux dev status    # Show dev mode status
dopemux dev enable    # Enable dev mode
dopemux dev disable   # Disable dev mode
```

---

### **Phase 2: Zen Dev Mode** (~45 min)

**A. Extract Zen as Submodule** (from original plan):
```bash
# Create separate repo
mkdir ~/zen-mcp-server-extraction
cp -r docker/mcp-servers/zen/zen-mcp-server/* ~/zen-mcp-server-extraction/
cd ~/zen-mcp-server-extraction
git init
git add .
git commit -m "Initial extraction from dopemux"
# Push to GitHub

# Add as submodule
cd ~/code/dopemux-mvp
git submodule add https://github.com/YOUR_ORG/zen-mcp-server.git external/zen-mcp-server
git commit -m "feat: extract Zen MCP as git submodule"
```

**B. Dev Path Detection**:
```python
# Update .claude.json generation:
zen_path = DevMode.get_component_path("zen") or Path("external/zen-mcp-server")

if "code/zen-mcp-server" in str(zen_path):
    console.print("[yellow]🔧 Using local Zen for development[/yellow]")

# Write to .claude.json:
claude_config["mcpServers"]["zen"]["cwd"] = str(zen_path)
```

**C. Contribution Docs**:
```markdown
# docs/CONTRIBUTING_ZEN.md

## Developing Zen MCP

1. Fork zen-mcp-server on GitHub
2. Clone: git clone git@github.com:YOU/zen-mcp-server ~/code/zen-mcp-server
3. Install: pip install -e ".[dev]"
4. Test: dopemux start (auto-detects your local Zen!)
5. Commit: git commit -m "feat: improve thinkdeep reasoning"
6. PR: Push and create pull request
```

---

### **Phase 3: Hot Reload** (~30 min)

**For Python MCP Servers** (Zen, ConPort):
```python
# In server.py or main loop:
if os.getenv("DOPEMUX_DEV_MODE") == "true":
    import watchdog
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class ReloadHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('.py'):
                console.print(f"[yellow]🔄 Reloading: {event.src_path}[/yellow]")
                # Reload module or restart server
                reload_server()

    observer = Observer()
    observer.schedule(ReloadHandler(), path=".", recursive=True)
    observer.start()
```

**For Docker Services**:
```yaml
# docker-compose.dev.yml
services:
  zen:
    volumes:
      # Mount local code for live editing
      - ${ZEN_DEV_PATH:-./external/zen-mcp-server}:/app
    environment:
      - HOT_RELOAD=true
    # Watchdog automatically reloads on changes
```

---

## 📋 Dev Mode Commands

### **dopemux dev** command group:

```bash
dopemux dev status              # Show dev mode status
dopemux dev enable              # Enable dev mode globally
dopemux dev disable             # Disable dev mode
dopemux dev paths               # Show detected dev paths
dopemux dev test-db             # Use test databases
dopemux dev reload <component>  # Hot reload component
```

**Example dopemux dev status**:
```
🔧 Development Mode Status

Dev Mode: ✅ ACTIVE
  Detected: pyproject.toml in current directory
  Test Databases: ✅ Enabled (~/.dopemux/dev/databases/)
  Log Level: DEBUG

Component Dev Paths:
  zen:     ~/code/zen-mcp-server ✅ (local development version)
  conport: Docker container (no local checkout)
  serena:  Docker container (no local checkout)

Skip Services: leantime, task-master, milvus

💡 To work on Zen:
   cd ~/code/zen-mcp-server
   Edit tools/thinkdeep.py
   dopemux dev reload zen
```

---

## 🗂️ Dev Mode Directory Structure

```
~/.dopemux/
├── config.yaml              # Production config
├── dev.yaml                 # Dev mode overrides
├── profiles/                # Production profiles
├── databases/               # Production databases
│   └── conport.db
└── dev/                     # Dev mode isolation
    ├── databases/           # Test databases
    │   ├── conport-test.db
    │   └── serena-test.db
    ├── logs/                # Dev logs
    └── cache/               # Dev cache

~/code/                      # Standard dev workspace
├── dopemux-mvp/             # Dopemux core (editable install)
├── zen-mcp-server/          # Zen fork (editable install)
├── conport-mcp/             # ConPort fork (optional)
└── serena-lsp/              # Serena fork (optional)
```

---

## 🔄 Hot Reload Implementation

### **Python MCP Servers** (Zen, ConPort):

```python
# server.py (at the top)
import os

DEV_MODE = os.getenv("DOPEMUX_DEV_MODE") == "true"

if DEV_MODE:
    # Enable watchdog for auto-reload
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import importlib

    class AutoReloader(FileSystemEventHandler):
        def __init__(self, modules_to_watch):
            self.modules_to_watch = modules_to_watch

        def on_modified(self, event):
            if event.src_path.endswith('.py'):
                # Reload modified module
                for module_name in self.modules_to_watch:
                    if module_name in event.src_path:
                        try:
                            module = sys.modules.get(module_name)
                            if module:
                                importlib.reload(module)
                                print(f"🔄 Reloaded: {module_name}")
                        except Exception as e:
                            print(f"⚠️  Reload failed: {e}")

    # Watch tools directory
    observer = Observer()
    observer.schedule(
        AutoReloader(['tools.thinkdeep', 'tools.planner', 'tools.consensus']),
        path="tools/",
        recursive=True
    )
    observer.start()
    print("🔧 Hot reload enabled (watching tools/)")
```

---

## 📊 Dev Mode vs Production Comparison

| Feature | Production | Dev Mode |
|---------|-----------|----------|
| **Zen Path** | external/zen-mcp-server (submodule) | ~/code/zen-mcp-server (local) |
| **Databases** | ~/.dopemux/databases/ | ~/.dopemux/dev/databases/ |
| **Logging** | INFO | DEBUG |
| **Hot Reload** | No | Yes (watchdog) |
| **Services** | All (15+ containers) | Core only (zen, conport, serena) |
| **Test Data** | Real decisions | Isolated test data |

---

## 🧪 Testing Workflow

### **For Zen MCP Development**:

```bash
# 1. Setup
cd ~/code/zen-mcp-server
pip install -e ".[dev]"
pip install pytest pytest-asyncio

# 2. Write tests
nano tests/test_thinkdeep.py

# 3. Run tests
pytest tests/test_thinkdeep.py -v

# 4. Test in dopemux
cd ~/test-project
export DOPEMUX_DEV_MODE=true
dopemux start
# Use thinkdeep in Claude Code, verify changes work

# 5. Commit
git commit -m "feat: improve thinkdeep confidence tracking"
```

### **For Dopemux Core**:

```bash
# 1. Edit code
nano src/dopemux/commands/decisions_commands.py

# 2. Run unit tests
pytest tests/test_decisions_commands.py

# 3. Test CLI directly
python -m dopemux decisions stats

# 4. Integration test
export DOPEMUX_DEV_MODE=true
dopemux init -p python-ml
dopemux profile show

# 5. Commit
git commit -m "feat: add decision filtering by energy level"
```

---

## 🎯 Implementation Priorities

### **Quick Win** (~15 min):
```python
# Just add dev mode detection to dopemux start
if Path("~/code/zen-mcp-server").expanduser().exists():
    zen_path = "~/code/zen-mcp-server"
    console.print("[yellow]🔧 Zen DEV MODE detected[/yellow]")
else:
    zen_path = "external/zen-mcp-server"

# Update .claude.json generation with detected path
```

### **Full Implementation** (~2 hours):
1. DevMode class (~30 min)
2. Extract Zen as submodule (~45 min)
3. Hot reload for Python servers (~30 min)
4. CONTRIBUTING_ZEN.md docs (~15 min)

---

## 💡 Design Decisions

### **Why ~/code/ as standard dev location?**
- Industry convention (most developers use ~/code/ or ~/dev/)
- Auto-detection works without env vars
- Clear separation from system installs

### **Why test databases for dev mode?**
- Don't pollute production ConPort with test decisions
- Safe experimentation
- Can be wiped and recreated easily

### **Why skip services in dev?**
- Faster startup (3 services vs 15+)
- Reduced resource usage
- Focus on what you're developing

### **Why hot reload?**
- Immediate feedback (no restart needed)
- Faster iteration
- Standard in modern dev tools

---

## 📚 Documentation Structure

### **For Users**: INSTALLATION.md ✅ (Done!)

### **For Dopemux Contributors**:
- `docs/CONTRIBUTING.md` - Dopemux core development
- Dev mode setup
- Testing guidelines
- Commit conventions

### **For Zen Contributors**:
- `docs/CONTRIBUTING_ZEN.md` - Zen MCP development
- How to fork and clone
- thinkdeep/planner/consensus architecture
- Testing Zen changes
- PR workflow

### **For MCP Server Contributors**:
- `docs/DEVELOPING_MCP_SERVERS.md` - Generic MCP dev guide
- Hot reload setup
- Testing patterns
- Integration with dopemux

---

## 🎯 Next Steps for Dev Mode

### **Immediate (Current Session?)**:
- [ ] Create DevMode class
- [ ] Add dev path detection to dopemux start
- [ ] Test Zen dev mode (if ~/code/zen-mcp-server exists)

### **Next Session**:
- [ ] Extract Zen as git submodule
- [ ] Write CONTRIBUTING_ZEN.md
- [ ] Implement hot reload
- [ ] dopemux dev commands

---

**Status**: Design complete, ready to implement
**Priority**: MEDIUM (nice-to-have for contributors, not blocking users)
**Estimated Time**: 2 hours → ~7 minutes at current velocity!
