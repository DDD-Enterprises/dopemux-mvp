# Next Session: Complete Multi-User Transformation

**Created**: 2025-10-18
**Previous Session**: Completed Phases A-B (foundation + ProfileManager)
**Remaining**: Phases C-F (~1 hour at current 18.7x velocity)

---

## ✅ What's Already Complete

### **ConPort Enhancement** (7 commits, 3,726 lines):
- 12 CLI commands operational (decisions, energy, patterns)
- Pattern learning active (Apriori algorithm, 6 patterns detected)
- Database enhanced (26 columns, 4 tables)
- Full test data (23 decisions, 6 energy logs)

### **Multi-User Foundation** (2 commits, 711 lines):
- ProfileManager class (config cascade, deep merge)
- 3 profile templates (python-ml, web-dev, adhd-default)
- Hardcoded paths removed (docker-compose, MCP wrappers)
- Template system (.claude.json.template)
- Complete architecture research and planning

---

## 🎯 Remaining Work (Phases C-F)

### **Phase C: Profile CLI Integration** (~30 min actual)

**Files to Create**:
```python
# src/dopemux/profile_commands.py (~150 lines)
@cli.group()
def profile():
    """Manage configuration profiles"""
    pass

@profile.command("list")
def list_profiles():
    """Show all available profiles"""
    manager = ProfileManager()
    profiles = manager.list_profiles()
    # Display with Rich table

@profile.command("use")
@click.argument("profile_name")
def use_profile(profile_name):
    """Set active profile for current workspace"""
    workspace = detect_workspace()
    manager = ProfileManager()
    manager.set_active_profile(workspace, profile_name)

@profile.command("show")
def show_profile():
    """Show active profile and merged config"""
    workspace = detect_workspace()
    manager = ProfileManager()
    config = manager.load_merged_config(workspace)
    # Display with Rich panel

@profile.command("create")
@click.argument("name")
@click.option("--based-on", help="Base profile to copy from")
def create_profile(name, based_on):
    """Create custom profile"""
    manager = ProfileManager()
    profile = manager.create_profile(name, "Custom profile", based_on)
```

**Integration**:
- Add to cli.py: Import and register profile group
- Use Click's ctx.obj to pass ProfileManager
- Store active profile in ctx.meta for other commands

**Testing**:
```bash
dopemux profile list
dopemux profile use python-ml
dopemux profile show
```

---

### **Phase D: Project Initialization** (~30 min actual)

**Files to Create**:
```python
# src/dopemux/project_init.py (~200 lines)
class ProjectInitializer:
    def __init__(self, workspace: Path, profile_manager: ProfileManager):
        self.workspace = workspace
        self.profile_manager = profile_manager

    def detect_project_type(self) -> str:
        """Auto-detect project type from markers"""
        # Check for pyproject.toml → python
        # Check for package.json → web
        # Check for Cargo.toml → rust
        # Return "unknown" if can't detect

    def initialize_project(self, profile_name: Optional[str] = None):
        """Run initialization wizard"""
        # 1. Detect or prompt for profile
        if not profile_name:
            detected = self.detect_project_type()
            profile_name = self._prompt_profile_selection(detected)

        # 2. Create .dopemux/ directory
        dopemux_dir = self.workspace / ".dopemux"
        dopemux_dir.mkdir(exist_ok=True)

        # 3. Copy profile as config.yaml
        profile = self.profile_manager.get_profile(profile_name)
        config_path = dopemux_dir / "config.yaml"
        # Write merged config

        # 4. Set active profile
        self.profile_manager.set_active_profile(self.workspace, profile_name)

        # 5. Create database directories
        (dopemux_dir / "databases").mkdir(exist_ok=True)

        # 6. Generate .claude.json from template
        self._generate_claude_config()

        # 7. Validate
        return self._validate_setup()
```

**CLI Command**:
```python
@cli.command()
@click.option("--profile", "-p", help="Profile to use")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing")
def init(profile, force):
    """Initialize dopemux in current project"""
    workspace = detect_workspace()
    initializer = ProjectInitializer(workspace, ProfileManager())
    initializer.initialize_project(profile)
```

**Testing**:
```bash
cd ~/test-project
dopemux init
# → Wizard: detect python → suggest python-ml → create .dopemux/
```

---

### **Phase E: Setup Automation** (~20 min actual)

**Files to Create**:
```bash
# scripts/setup.sh (~300 lines)
#!/bin/bash
set -e

echo "🚀 Dopemux Setup - ADHD-Optimized Development Platform"

# 1. Check prerequisites
check_command() {
    command -v $1 >/dev/null 2>&1 || {
        echo "❌ Required: $1. Install and retry."
        exit 1
    }
}

check_command docker
check_command git
check_command python3

# 2. Setup ~/.dopemux/
echo "📁 Creating ~/.dopemux/ directory..."
mkdir -p ~/.dopemux/{profiles,databases,cache}

# 3. Install default profiles
echo "📋 Installing default profiles..."
python3 -c "from src.dopemux.profile_manager import ProfileManager; ProfileManager().install_default_profiles()"

# 4. Setup .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Edit .env and add your API keys!"
    echo "   Required: OPENAI_API_KEY, VOYAGEAI_API_KEY"
fi

# 5. Install Python package (editable)
echo "📦 Installing dopemux package..."
pip install -e .

# 6. Initialize git submodules (Zen MCP)
echo "🔧 Initializing Zen MCP submodule..."
git submodule update --init --recursive

# 7. Create Docker network
docker network create dopemux-unified-network 2>/dev/null || true

# 8. Start MCP services
echo "🐳 Starting MCP services..."
docker-compose -f docker/mcp-servers/docker-compose.yml up -d

# 9. Wait for health
echo "⏳ Waiting for services to be healthy..."
sleep 10

# 10. Verify
dopemux health

echo "✅ Setup complete!"
echo "   Run: dopemux start"
```

**Testing**:
```bash
# On fresh machine:
git clone https://github.com/YOUR_ORG/dopemux-mvp.git
cd dopemux-mvp
./scripts/setup.sh
# → All set up automatically
```

---

### **Phase F: Zen Submodule** (~20 min actual)

**Steps**:
```bash
# 1. Create separate zen-mcp-server repo
mkdir ~/zen-mcp-server-extraction
cp -r docker/mcp-servers/zen/zen-mcp-server/* ~/zen-mcp-server-extraction/
cd ~/zen-mcp-server-extraction
git init
git add .
git commit -m "Initial extraction from dopemux"
# Push to GitHub: YOUR_ORG/zen-mcp-server

# 2. Add as submodule to dopemux
cd ~/code/dopemux-mvp
mkdir -p external
git submodule add https://github.com/YOUR_ORG/zen-mcp-server.git external/zen-mcp-server

# 3. Update docker/mcp-servers/zen/Dockerfile
# Change: COPY zen-mcp-server/ .
# To: COPY ../../external/zen-mcp-server/ .

# 4. Update .claude.json template
# Change: ${DOPEMUX_WORKSPACE}/docker/mcp-servers/zen/zen-mcp-server
# To: ${ZEN_MCP_PATH} (with detection logic)

# 5. Dev mode detection in dopemux start
if [ -d ~/code/zen-mcp-server ]; then
    export ZEN_MCP_PATH=~/code/zen-mcp-server
    echo "🔧 Zen DEV MODE: Using ~/code/zen-mcp-server"
else
    export ZEN_MCP_PATH=${DOPEMUX_WORKSPACE}/external/zen-mcp-server
fi
```

**Contribution Workflow**:
```bash
# Fork zen-mcp-server on GitHub
git clone git@github.com:YOUR_USER/zen-mcp-server.git ~/code/zen-mcp-server
cd ~/code/zen-mcp-server
pip install -e ".[dev]"

# Work on Zen
# Edit tools/thinkdeep.py, tools/planner.py, tools/consensus.py

# Test with dopemux (auto-detects your local version!)
cd ~/any-project-using-dopemux
dopemux start
# Uses ~/code/zen-mcp-server automatically

# Contribute back
git checkout -b feature/improve-thinkdeep
git commit -m "feat: improve thinkdeep reasoning chains"
git push origin feature/improve-thinkdeep
# Create PR to zen-mcp-server repo
```

---

## 📋 Detailed Task Breakdown

### **Task 1: Profile CLI Commands** (30 min)
- [ ] Create src/dopemux/profile_commands.py
- [ ] Import ProfileManager
- [ ] Implement list/use/create/show commands
- [ ] Add Rich formatting for output
- [ ] Register in cli.py
- [ ] Test all 4 commands

### **Task 2: Init Wizard** (30 min)
- [ ] Create src/dopemux/project_init.py
- [ ] Implement project type detection (check markers)
- [ ] Build interactive wizard with Click prompts
- [ ] Generate .dopemux/config.yaml from profile
- [ ] Create database directories
- [ ] Generate .claude.json from template
- [ ] Add validation checks

### **Task 3: Setup Script** (20 min)
- [ ] Create scripts/setup.sh
- [ ] Add prerequisite checks (docker, git, python)
- [ ] Create ~/.dopemux/ structure
- [ ] Install profiles
- [ ] Generate .env
- [ ] pip install -e .
- [ ] Docker network + services
- [ ] Health validation

### **Task 4: Zen Submodule** (30 min)
- [ ] Extract zen-mcp-server to separate repo
- [ ] git submodule add external/zen-mcp-server
- [ ] Update Dockerfile paths
- [ ] Add dev mode detection logic
- [ ] Update .gitignore
- [ ] Test both modes (submodule + dev)

### **Task 5: Documentation** (30 min)
- [ ] Write docs/INSTALLATION.md
- [ ] Write docs/MULTI_PROJECT.md
- [ ] Write docs/PROFILES.md
- [ ] Write docs/CONTRIBUTING_ZEN.md
- [ ] Update README.md with new installation
- [ ] Add Quick Start section

### **Task 6: Testing** (20 min)
- [ ] Clone on fresh directory
- [ ] Run setup.sh
- [ ] dopemux init in test project
- [ ] Verify all commands work
- [ ] Test profile switching
- [ ] Test Zen dev mode

---

## 🚀 Quick Start Commands (After Implementation)

**For New Users**:
```bash
git clone https://github.com/dopemux/dopemux-mvp.git
cd dopemux-mvp
./scripts/setup.sh
# Edit .env with API keys
dopemux health
```

**For New Projects**:
```bash
cd ~/my-project
dopemux init
# Select: python-ml
dopemux start
```

**For Zen Contributors**:
```bash
git clone git@github.com:YOUR_USER/zen-mcp-server.git ~/code/zen-mcp-server
cd ~/code/zen-mcp-server
pip install -e ".[dev]"
# dopemux auto-detects and uses your local version!
```

---

## 💎 Architecture Summary

**Config Cascade** (Click context + YAML deep merge):
- Global defaults → Profile settings → Project overrides → Env vars

**Workspace Detection** (Reuse dope-context pattern):
- Git root → pyproject.toml → package.json → cwd

**Database Strategy** (Hybrid):
- Shared: ~/.dopemux/databases/conport.db (cross-project learning!)
- Local: .dopemux/databases/{tool}-{hash}.db (privacy)

**Zen Structure** (Submodule + dev mode):
- Production: external/zen-mcp-server (submodule)
- Dev: ~/code/zen-mcp-server (auto-detected first)

---

**Status**: Foundation complete, ready for Phases C-F implementation
**Next Session**: Start with Task 1 (profile CLI commands)